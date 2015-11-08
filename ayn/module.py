import sys
sys.path.insert(0, 'libs')
import oauth2
import json
from datetime import datetime
from dateutil import parser
import logging


class ModuleFactory:
	class __ModuleFactory:
		def __init__(self):
			pass
		def __str__(self):
			return repr(self)
	instance = None
	modules = {}
	def __init__(self):
		if not ModuleFactory.instance:
			ModuleFactory.instance = ModuleFactory.__ModuleFactory()

	def register_module(self, source, module):
		self.modules[source] = module

	def get_news(self, source, token, amount, offset):
		if source in self.modules.keys():
			return self.modules[source].get_news(token, amount, offset)


class TwitterModule:
	CONSUMER_KEY = 'FQhc0HUHu6eDymxbrls4lUDKL'
	CONSUMER_SECRET = 'rzmoEgKvhgsdGX6zgwodLH7YUyG6odrgOHZnQxkC5Bwo0hVKZi'
	url =  'https://api.twitter.com/1.1/statuses/home_timeline.json'
	lastid = 0
	def __init__(self):
		ModuleFactory().register_module('twitter', self)

	def get_news(self, token, amount, offset):
		body = 'count=' + str(amount)															#TODO: offset
		print('token ' + str(token))
		consumer = oauth2.Consumer(key=self.CONSUMER_KEY, secret=self.CONSUMER_SECRET) 
		client = oauth2.Client(consumer, oauth2.Token(key=token[0], secret=token[1]))
		resp, content = client.request(self.url, method='GET', body=body, headers=None)
		tweets = json.loads(content)
		# time_format = '%a %b %d %H:%M:%S %z %Y'												# Wed Mar 03 19:37:35 +0000 2010
		logging.info(tweets)
		data = []					# id=5129512190738432	^8#w%O>R5d3s>vB7o&B,J7I^Zm~
		for tweet in tweets:
			time = parser.parse(tweet['created_at'])
			time = time.replace(tzinfo=None)
			data.append({'content' : str(tweet), 'time' : (time - datetime(1970,1,1)).total_seconds(), 'source' : 'twitter'})
		return data

# class RedditModule:
# 	CONSUMER_KEY = 'LFBR3WSQCrOt6g'
# 	CONSUMER_SECRET = 'H35OVobtd4K0YKIl8StDffr4jm0'
# 	url = 'https://oauth.reddit.com'
# 	def __init__(self):
# 		ModuleFactory().register_module('reddit', RedditModule)

# 	def get_news(self, token):
# 		consumer = oauth2.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
# 		client = oauth2.Client(consumer, token)
# 		resp, content = client(url, method='GET', )