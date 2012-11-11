"""
Module contains access to the twitter api and passing on incoming 
tweets to the SpellChecker.
"""

import tweepy, re, json, nltk, threading, time

CONSUMER_KEY = 'cvJJSMjnSthBvTnfidy9Lg'
CONSUMER_SECRET = 'EbXCAJug2XRFjybaWVYD6UDT9myeWG7QG0EI39jwUw4'
ACCESS_TOKEN = '38526467-RayXlh3A2OncJJAHnU4Jfj5X9QDyylPFvcSwiLRsz'
ACCESS_TOKEN_SECRET = '86OPKYknQWMRNk3eF9wpoTTgGTAiLbT6D30QDiM6k'


class TweetSpellChecker(threading.Thread):
	"""Starts a thread for each location defined and starts retrieving tweets for each location and passes them on to the SpellChecker"""

	def __init__(self, location):
		super(TweetSpellChecker, self).__init__()
		self.auth1 = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
		self.auth1.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
		self.statistics = {}
		self.tweet_retrievers = []
		self.locations = location
		for k, v in self.locations.iteritems():
			self.statistics[k] = Statistics(k)

	def run(self):
		"""Start a thread for each given location and keep each thread for later access."""
		for query,loc in self.locations.iteritems():
			geocode = '%s,%s,%s' % loc
			t = RepeatingTweetRetriever(7, query, geocode, SpellChecker(self.statistics[query]))
			t.start()
			self.tweet_retrievers.append(t)

	def get_statistics(self):
		"""Get Statistics for the given locations."""
		return self.statistics

	def stop(self):
		"""Stop this thread and all containing threads."""
		for t in self.tweet_retrievers:
			t.stop()
			t.join()
		self._Thread__stop()


class RepeatingTweetRetriever(threading.Thread):
	"""Access Twitter api periodically and retrieve tweets according to the specified location. Passes on the retrieved tweets to the actual SpellChecker which performs the cleaning and spell checking of tweets."""

	def __init__(self, interval, query, geocode, spell_checker):
		threading.Thread.__init__(self)
		self.interval = interval
		self.query = query
		self.geocode = geocode
		self.spell_checker = spell_checker
		self.max_id = 999999999999999999
		self._stop = threading.Event()
		self.get_tweets()

	def run(self):
		while not self._stop.is_set():
			t = threading.Timer(self.interval, self.get_tweets)
			t.start()
			t.join()

	def get_tweets(self):
		"""Retrieve tweets form twitter api."""
		res = tweepy.api.search(q=self.query, rpp=100, max_id=self.max_id, geocode=self.geocode, include_entities=True)
		t_id = self.max_id
		for r in res:
			t_id = min(t_id, r.id)
			self.spell_checker.check_tweet(r.text)
			if self._stop.is_set():
				break
		self.max_id = t_id-1

	def stop(self):
		"""Stop retrieving and processing of tweets"""
		self._stop.set()


class SpellChecker(object):
	"""Class to clean and  spell check all incoming tweets"""

	def __init__(self, stat):
		super(SpellChecker, self).__init__()
		self.stat = stat
		dict_file = open("en-GB-wlist.txt", "r")
		all_words = dict_file.readlines()
		self.word_dict = {}
		for word in all_words:
			word = word.rstrip('\n')
			index = word[0]
			index = index.lower()
			if not self.word_dict.has_key(index):
				self.word_dict[index] = {}
			if not self.word_dict[index].has_key(len(word)):
				self.word_dict[index][len(word)] = []
			self.word_dict[index][len(word)].append(word)

	def edit_dist(self, a, b):
		"Calculates the Levenshtein distance between a and b."
		n, m = len(a), len(b)
		if n > m:
			# Make sure n <= m, to use O(min(n,m)) space
			a,b = b,a
			n,m = m,n
		current = range(n+1)
		for i in range(1,m+1):
			previous, current = current, [i]+[0]*n
			for j in range(1,n+1):
				add, delete = previous[j]+1, current[j-1]+1
				change = previous[j-1]
				if a[j-1] != b[i-1]:
					change = change + 1
				current[j] = min(add, delete, change)

		return current[n]

	def is_special_word(self, word):
		"""check if word in tweets is a hashtag, username, hyperlink, email address, retweet (return True if word is special)"""
		return word[0] == '#' or word[0] == '@' or word == 'RT' or re.match(r'(https://|http://)', word) != None or re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', word) != None
			
	def clean_word(self, word):
		"""Clean each word by seperating words that are connected by a special character (i.e. days/weeks -> [days, weeks]) and removing special characters at the beginning and end of the word."""
		match = re.match(r'([\d\w]+)([/_\-\+\.!?,\(\)]+)([\d\w]+)', word)
		ret = []
		if  match != None:
			for m in match.groups():
				ret.append(re.sub(r'^([-_\'\"\W\d]+)|([-_\'\"\W]+)$', '', m))
		else:
			ret.append(ret.append(re.sub(r'^([-_\'\"\W\d]+)|([-_\'\"\W]+)$', '', word)))
		return ret

	def clean_tweet(self, tweet):
		"""Clean incoming tweet by removing special tweet words, named entities, (returns a list containg all words of the tweet that were not removed)"""
		# tokenize sentences
		named_entity = []
		for sent in nltk.sent_tokenize(tweet):
			# tokenize words in sentence and tag them 
			for chunk in nltk.chunk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
				if hasattr(chunk, 'node'):
					named_entity.append(''.join([child[0] for child in chunk]))

		split_tweet = re.split(r'\s+', tweet)
		without_special = []
		for s in split_tweet:
			if (not self.is_special_word(s) and not s in named_entity):
				without_special += self.clean_word(s)
		without_special = filter(None, without_special)
		return 	without_special
		
	def check_tweet(self, tweet):
		"""Spell checks the actual tweet by looking in the dictionary if the words in the tweet actually exists, if not it counts as an error. Save some statstics about the tweets."""
		cleaned_tweet = self.clean_tweet(tweet)		
		tweet_error = 0.0
		word_error = 0
		if len(cleaned_tweet) > 0:
			for word in cleaned_tweet:
				self.stat.word_length(len(word))
				min_word_error = float("inf")
				index = word[0]
				index = index.lower()
				if self.word_dict.has_key(index) and self.word_dict[index].has_key(len(word)):
					check_list = self.word_dict[index][len(word)]
					if word in check_list or word.lower() in check_list: #check_list.has_key(word) or check_list.has_key(word.lower()):
						min_word_error = 0.0
						min_word = word
					else:
						tweet_error += 1.0
						self.stat.add_wrong_word(word)
						for cw in check_list:
							dist = self.edit_dist(word, cw)
							if  dist < min_word_error:
								min_word = cw
								min_word_error = dist
				else:
					tweet_error += 1
					self.stat.add_wrong_word(word)
					min_word_error = len(word)

				if min_word_error < float("inf"):
					word_error = word_error + min_word_error
			self.stat.tweet_checked()
			self.stat.set_avg_tweet_error(tweet_error/len(cleaned_tweet))
			self.stat.set_avg_word_error(word_error/len(cleaned_tweet))
			self.stat.tweet_length(len(cleaned_tweet))



class Statistics(object):
	"""Class to keep simple statistics about the tweets checked by the SpellChecker. """
	def __init__(self, name):
		super(Statistics, self).__init__()
		self.tweets_checked = 0
		self.sum_tweet_error = 0.0
		self.sum_word_error = 0.0
		self.avg_tweet_error = 0.0
		self.avg_word_error = 0.0
		self.max_tweet_error = 0.0
		self.min_tweet_error = 100000
		self.avg_tweet_length = 0
		self.sum_tweet_length = 0
		self.avg_word_length = 0
		self.sum_word_length = 0
		self.number_words = 0
		self.name = name
		self.wrong_words = {}


	def tweet_checked(self):
		"""Increase number of tweets checked."""
		self.tweets_checked += 1

	def set_avg_tweet_error(self, error):
		"""Update the average error per tweet."""
		self.sum_tweet_error += error
		self.avg_tweet_error = self.sum_tweet_error/self.tweets_checked

	def set_avg_word_error(self, error):
		"""Update the average error per word in tweet."""
		self.sum_word_error += error
		self.avg_word_error = self.sum_word_error/self.tweets_checked

	def tweet_length(self, length):
		"""Update the average tweet length."""
		self.sum_tweet_length += length
		self.avg_tweet_length = self.sum_tweet_length/self.tweets_checked

	def word_length(self, length):
		"""Update the average word length."""
		self.number_words += 1
		self.sum_word_length += length
		self.avg_word_length = self.sum_word_length/self.number_words

	def add_wrong_word(self, word):
		"""Add a misspelled word."""
		if self.wrong_words.has_key(word):
			self.wrong_words[word] = self.wrong_words[word] + 1
		else:
			self.wrong_words[word] = 1

	def get_wrong_words(self):
		"""Return list of misspelled words sorted according to most occurring misspelled word."""
		return sorted(self.wrong_words, key=self.wrong_words.__getitem__, reverse=True)
