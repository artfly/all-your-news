import sys
sys.path.insert(0, 'libs')
import oauth2
from datetime import datetime
from dateutil import parser
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
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

	CONSUMER_KEY = 'FQhc0HUHu6eDymxbrls4lUDKL'
	CONSUMER_SECRET = 'rzmoEgKvhgsdGX6zgwodLH7YUyG6odrgOHZnQxkC5Bwo0hVKZi'

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
		url =  'https://api.twitter.com/1.1/statuses/home_timeline.json'
		token = (db_token.token_key, db_token.token_secret)
		offset = db_token.offset
		count = request.count
		max_id = ''
		consumer = oauth2.Consumer(key=self.CONSUMER_KEY, secret=self.CONSUMER_SECRET) 
		client = oauth2.Client(consumer, oauth2.Token(key=db_token.token_key, secret=db_token.token_secret))
		lastpost = count + offset - 1
		iterations = int(lastpost / 200) + 1
		data = []

		for i in range(0, iterations):
			body = 'count=200'
			resp, content = client.request(url, method='GET', body=body, headers=None)
			tweets = json.loads(content)
			returned_posts = len(tweets)
			if 'errors' in tweets:
				break															
			# posts = self.r.request_json(url='https://oauth.reddit.com/', params={'limit' : '100', 'after' : after})
			if offset < returned_posts * (i + 1):
				to = (lastpost + 1) if lastpost < returned_posts else returned_posts
				for j in range(offset % returned_posts, to):
					tweet = tweets[j]
					logging.info(str(tweet))
					time = parser.parse(tweet['created_at'])
					time = time.replace(tzinfo=None)
					data.append(News(content=str(tweet), time=str((time - datetime(1970,1,1)).total_seconds()), source='twitter'))
					logging.info(str((time - datetime(1970,1,1)).total_seconds()))
				offset = 0
			lastpost -= returned_posts
			max_id = tweets[returned_posts - 1]['id']
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