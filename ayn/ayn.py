import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb
from operator import itemgetter
import password as pwd
import json
import module_factory
import logging
import time


ayn_api = endpoints.api(name='ayn', version='v1')



class Token(messages.Message):
	source = messages.StringField(1, required=True)
	token = messages.StringField(2, required=True)


class TokenCollection(messages.Message):
	sources = messages.MessageField(Token, 1, repeated=True)


class TokenMessage(messages.Message):
	token = messages.MessageField(Token, 1)

class News(messages.Message):
	source = messages.StringField(1)
	content = messages.StringField(2)


class NewsCollection(messages.Message):
	feed = messages.MessageField(News, 1, repeated=True)


class UserMessage(messages.Message):
	userid = messages.IntegerField(1)
	password = messages.StringField(2)

class EmptyMessage(messages.Message):
	pass

class TokenModel(ndb.Model):
	source = ndb.StringProperty()
	token = ndb.JsonProperty(indexed=True)


class User(ndb.Model):
	password = ndb.StringProperty()
	token = ndb.StructuredProperty(TokenModel)
	sources = ndb.StringProperty(repeated=True)



@ayn_api.api_class(resource_name='users')
class UsersApi(remote.Service):
	"""Users API v1"""
	# factory = None

	USER_METHOD_RESOURCE = endpoints.ResourceContainer(Token)

	@endpoints.method(USER_METHOD_RESOURCE, UserMessage,
						path='users', http_method='POST', name='postUser')
	def post_user(self, request):
		token = TokenModel(source=request.source, token=request.token)
		user = User.query(User.token.token == token.token).get()
		if user is None:
			user = User(password=pwd.mkpassword(), token=token)
		user_key = user.put()
		return UserMessage(userid=user_key.integer_id(), password=user.password)

	SOURCES_METHOD_RESOURCE = endpoints.ResourceContainer(Token, userid=messages.IntegerField(2, required=True))

	@endpoints.method(SOURCES_METHOD_RESOURCE, EmptyMessage,
						path='users/{userid}/sources', http_method='POST', name='postSource')
	def post_source(self, request):
		factory = module_factory.ModuleFactory()
		basic_auth = self.request_state.headers.get('authorization')
		logging.info("basic oauth : " + str(basic_auth))
		logging.info("request.userid : " + str(request.userid))
		user = User.get_by_id(request.userid)
		logging.info("user's passwo " + str(user.password))
		if user is None:
			raise endpoints.BadRequestException("No such user")
		elif user.password != basic_auth:
			raise endpoints.BadRequestException("Invalid password")
		factory.post_token(request.source, request.token, request.userid)
		if request.source not in user.sources:
			logging.info(user.sources)
			logging.info(request.source)
			user.sources.append(request.source)
		user.put()
		return EmptyMessage()

	NEWS_METHOD_RESOURCE = endpoints.ResourceContainer(count=messages.IntegerField(1, default=15),
	 								since=messages.IntegerField(2, default=0), userid=messages.IntegerField(3, required=True))

	@endpoints.method(NEWS_METHOD_RESOURCE, NewsCollection,
						path='users/{userid}/news', http_method='GET', name='getNews')
	def get_news(self, request):
		basic_auth = self.request_state.headers.get('authorization')
		user = User.get_by_id(request.userid)
		if user is None:
			raise endpoints.BadRequestException("No such user")
		elif user.password != basic_auth:
			raise endpoints.BadRequestException("Invalid password")
		factory = module_factory.ModuleFactory()
		news_collection = NewsCollection(feed=[])
		items = []
		since = request.since if request.since != 0 else int(time.time())
		logging.info(request.count)
		for source in user.sources:
			feed = factory.get_news(source, request.userid, request.count, since)
			items.extend(feed)
		items = sorted(items, key=itemgetter('time'), reverse=True)
		items = items[:request.count]
		for news in items:
			n = News(source=news['source'], content=str(news['content']))
			news_collection.feed.append(n)
		return news_collection

APPLICATION = endpoints.api_server([UsersApi])





