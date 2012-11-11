#Twitter Wars: Spell checking tweets from two locations and comparing results

##Approach
The results can be seen on the website which was created using webpy (http://webpy.org/ ,  https://github.com/webpy/webpy). The spell checking can be started and stopped. Results are updated automatically.

For accessing the Twitter API the python library tweepy (https://github.com/tweepy/tweepy) is used. Tweepy's search function is used to perform a search for the two specified locations (London, Exeter). For each location a thread is started which performs the search requests periodically. The locations are specified by their GPS coordinates and a radius (for both locations 20 miles. To retrieve tweets that have not been retrieved yet the max_id parameter of the twitter search api is used meaning that first the most recent tweets are retrieved, with each search request the tweets get older. 
Every time a request is performed the retrieved tweets are spell checked. For spell checking first the tweets are cleaned form hasthags, usernames, email addresses, links and RT (retweets). Furthermore words are checked if they contain special characters like '"-_ etc. at the beginning and/or end and removed when necessary. The language processing library nltk (http://nltk.org/) is used to perform chunking and then named entity recognition. Named entities are also excluded from spell checking. 
To check tweets if they are spelled correctly a dictionary of 127238 english words is used. If a word is contained in the dictionary it is spelled correctly, is the word not contained it is counted as one error in the tweet. To get the error in the word the word the levensthein distance (edit distance) to all words within the dictionary that start with the same character and are of the same length is calculated and the minimal distance defines the error for the respective word. 

To make the results comparable the average tweet error and average word error is calculated and updated periodically on the website.


##Results
After checking about 4500 tweets for each location the results show that Exeter is better at spelling than London.

Results for London:  
Average Tweet Error: 9.67244140978 % of words wrong equal to 1.396855508 words per tweet  
Average Word Error: 24.3149112587 % characters wrong per word equal to 0.972596450348 characters per word  
Average Word Length: 4  
Tweets Checked: 4465   
Average Tweet Length: 11 words per tweet  

Results for Exeter:  
Average Tweet Error: 6.579882097 % of words wrong equal to 0.78958585164 words per tweet  
Average Word Error: 15.6104273598 % characters wrong per word equal to 0.624417094393 characters per word  
Average Word Length: 4  
Tweets Checked: 4550   
Average Tweet Length: 12 words per tweet   

##Usage
The libraries webpy and tweepy are already included. nltk has to be installed on your system (http://nltk.org/install.html). 

The program can be started by navigating to the downloaded folder and  typing "python gui_tweetspellchecker.py" in the commandline. This starts the webserver which is reachable through the browser (http://localhost:8080 ) 

