"""
Module performs the interaction between the website and the backend whicht performs the actual retrieving of tweets and spell checking.
Results are refreshed dynamically every few secods via javascript.
"""

import web, twitterspellcheck

urls = (
	'/', 'index',
	'/start', 'start',
	'/update', 'update',
	'/stop', 'stop'
	)

render = web.template.render('templates/')

locations = {'Exeter' : (50.720373,-3.531521, '20mi'), 'London' : (51.517289,-0.115562, '20mi')}
tweet_spell_checker = None
is_running = False

class index(object):
	"""Start page for TweetSpellChecker"""
	
	def GET(self):
		# todos = db.select('todo')
		return render.index("")


class start(object):
	"""Start Spell checking"""

	def GET(self):
		global tweet_spell_checker, is_running
		if tweet_spell_checker == None:
			is_running = True
			tweet_spell_checker = twitterspellcheck.TweetSpellChecker(locations)
			tweet_spell_checker.start()
		return render.update([], "Spell checking started. Page will be updated with new results every few seconds.")

class update(object):
	"""Update results interactively"""

	def GET(self):
		global tweet_spell_checker, is_running
		if is_running and tweet_spell_checker != None:
			return render.update(tweet_spell_checker.get_statistics(), None)
		else:
			return render.update([], "Something went wrong")

class stop(object):
	"""Stop Spell checking"""

	def GET(self):
		global tweet_spell_checker, is_running
		is_running = False
		if tweet_spell_checker != None:
			tweet_spell_checker.stop()
			tweet_spell_checker.join()
			stats = tweet_spell_checker.get_statistics()
			tweet_spell_checker = None
			return render.update(stats, "Spell checking finished.")
		else:
			return render.update([], "Something went wrong")




if __name__ == '__main__':
	app = web.application(urls, globals())
	app.run()
		