import sys
sys.path.insert(0, 'libs')
import tweepy
from datetime import datetime
from dateutil import parser
import endpoints
from protorpc import remote
from google.appengine.ext import ndb
from ayn_module import BaseModuleApi
import ayn_module
import ast
import json
import httplib
import logging


module_api = endpoints.api(name='module', version='v1')

class TokenDB(ndb.Model):
	token_key = ndb.StringProperty()
	token_secret = ndb.StringProperty()

class RawJsonParser(tweepy.parsers.Parser):
    def parse(self, method, payload):
        return payload


@module_api.api_class(resource_name='users')
class ModuleApi(BaseModuleApi):
	"""Module API v1"""

	CONSUMER_KEY = 'pjBmdH8twx7RKX91CyBosaZOo'
	CONSUMER_SECRET = 'UO7kzSoaGMflKsLWtolzmud7iSJRS0cyW0U3ID5ytmpdTSJl2f'

	@endpoints.method(BaseModuleApi.SOURCES_METHOD_RESOURCE, ayn_module.EmptyMessage,
						path='users/{userid}/tokens', http_method='POST', name='postSource')
	def post_token(self, request):
		token = ast.literal_eval(request.token)
		if 'token_key' in token and 'token_secret' in token:
			token_key = token['token_key']
			token_secret = token['token_secret']
			db_token = TokenDB.get_by_id(request.userid)
			if db_token is None:
				db_token = TokenDB(id=request.userid)
			db_token.token_secret = token_secret
			db_token.token_key = token_key
			db_token.put()
		else:
			raise endpoints.BadRequestException("Invalid token")
		return ayn_module.EmptyMessage() 

	@endpoints.method(BaseModuleApi.NEWS_METHOD_RESOURCE, ayn_module.NewsCollection,
						path='users/{userid}/news', http_method='GET', name='getNews')
	def get_news(self, request):
		db_token = TokenDB.get_by_id(request.userid)
		if db_token is None:
			raise endpoints.BadRequestException("No such user")
		token = (db_token.token_key, db_token.token_secret)
		since = request.since
		count = request.count
		max_id = None
		returned_posts = 0
		taken = 0
		data = []
		auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET)
		auth.set_access_token(token[0], token[1])
		api = tweepy.API(auth_handler=auth, parser=RawJsonParser())
		try:
			while True:
				if max_id != None:
					tweets = api.home_timeline(count=200, max_id=max_id)
				else:
					tweets = api.home_timeline(count=200)
				tweets = json.loads(tweets)
				for tweet in tweets:
					if taken == count:
						return ayn_module.NewsCollection(feed=data)
					time = parser.parse(tweet['created_at']).replace(tzinfo=None)
					time = str((time - datetime(1970,1,1)).total_seconds())
					if time > since:
						data.append(ayn_module.News(content=json.dumps(tweet), time=time, source='twitter'))
						taken += 1
				max_id = tweets[len(tweets) - 1]['id_str']
		except tweepy.error.TweepError as e:
			logging.info(e.message)
			# info = json.loads(e.message[0])
			# logging.info(info)
			raise endpoints.BadRequestException(e.message)
		logging.info("here")
		return ayn_module.NewsCollection(feed=data)


APPLICATION = endpoints.api_server([ModuleApi])