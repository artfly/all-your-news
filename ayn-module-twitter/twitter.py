import sys
sys.path.insert(0, 'libs')
import tweepy
from datetime import datetime
from dateutil import parser
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb
import ast
import json
import logging


module_api = endpoints.api(name='module', version='v1')


class Token(messages.Message):
	token = messages.StringField(1, required=True)


class News(messages.Message):
	source = messages.StringField(1)
	time = messages.StringField(2)
	content = messages.StringField(3)


class NewsCollection(messages.Message):
	feed = messages.MessageField(News, 1, repeated=True)


class EmptyMessage(messages.Message):
	pass

class TokenDB(ndb.Model):
	token_key = ndb.StringProperty()
	token_secret = ndb.StringProperty()
	offset = ndb.IntegerProperty(default=0)


@module_api.api_class(resource_name='users')
class UsersApi(remote.Service):
	"""Users API v1"""

	CONSUMER_KEY = 'pjBmdH8twx7RKX91CyBosaZOo'
	CONSUMER_SECRET = 'UO7kzSoaGMflKsLWtolzmud7iSJRS0cyW0U3ID5ytmpdTSJl2f'

	SOURCES_METHOD_RESOURCE = endpoints.ResourceContainer(Token, userid=messages.IntegerField(2, required=True))

	@endpoints.method(SOURCES_METHOD_RESOURCE, EmptyMessage,
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
		return EmptyMessage() 


	NEWS_METHOD_RESOURCE = endpoints.ResourceContainer(
								userid=messages.IntegerField(1, required=True), count=messages.IntegerField(2, required=True))

	@endpoints.method(NEWS_METHOD_RESOURCE, NewsCollection,
						path='users/{userid}/news', http_method='GET', name='getNews')
	def get_news(self, request):
		db_token = TokenDB.get_by_id(request.userid)
		if db_token is None:
			raise endpoints.BadRequestException("No such user")
		token = (db_token.token_key, db_token.token_secret)
		offset = db_token.offset
		count = request.count
		max_id = None
		lastpost = count + offset - 1
		iterations = int(lastpost / 200) + 1
		returned_posts = 0
		data = []
		auth = tweepy.OAuthHandler(self.CONSUMER_KEY, self.CONSUMER_SECRET)
		auth.set_access_token(token[0], token[1])
		api = tweepy.API(auth)
		try:
			while True:
				if max_id != None:
					tweets = api.home_timeline(count=200, max_id=max_id)
				else:
					tweets = api.home_timeline(count=200)
				returned_posts += len(tweets)															
				if offset < returned_posts:
					to =  (lastpost + 1) % len(tweets) if lastpost < returned_posts else len(tweets)
					for j in range(offset % len(tweets), to):
						tweet = tweets[j]
						time = parser.parse(tweet.created_at)
						# logging.info(time)
						time = time.replace(tzinfo=None)
						data.append(News(content=str(vars(tweet)), time=str((time - datetime(1970,1,1)).total_seconds()), source='twitter'))
					offset = 0
					if lastpost < returned_posts:
						break
				max_id = tweets.max_id
		except tweepy.error.TweepError as e:
			raise endpoints.BadRequestException(e.message[0]['message'])
		return NewsCollection(feed=data)


	OFFSET_METHOD_RESOURCE = endpoints.ResourceContainer(
								userid=messages.IntegerField(1, required=True), offset=messages.IntegerField(2, required=True))

	@endpoints.method(OFFSET_METHOD_RESOURCE, EmptyMessage,
						path='users/{userid}/offset', http_method='POST', name='postOffset')
	def post_offset(self, request):
		db_token = TokenDB.get_by_id(request.userid)
		if db_token is None:
			raise endpoints.BadRequestException("No such user")
		db_token.offset = request.offset
		db_token.put()
		return EmptyMessage()


APPLICATION = endpoints.api_server([UsersApi])