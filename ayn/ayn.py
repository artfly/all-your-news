import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb
from operator import itemgetter
import password as pwd
import json
import module
import logging


ayn_api = endpoints.api(name='ayn', version='v1')



class Token(messages.Message):
	source = messages.StringField(1, required=True)
	key = messages.StringField(2, required = True)
	secret = messages.StringField(3, required = True)


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
	key = ndb.StringProperty()
	secret = ndb.StringProperty()

class User(ndb.Model):
	password = ndb.StringProperty()
	registered_token = ndb.StructuredProperty(TokenModel)
	tokens = ndb.StructuredProperty(TokenModel, repeated=True)



@ayn_api.api_class(resource_name='users')
class UsersApi(remote.Service):
	"""Users API v1"""

	USER_METHOD_RESOURCE = endpoints.ResourceContainer(Token)

	@endpoints.method(USER_METHOD_RESOURCE, UserMessage,
						path='users', http_method='POST', name='postUser')
	def post_user(self, request):
		token = TokenModel(source=request.source, key=request.key, secret=request.secret)
		user = User.query(User.registered_token == token).get()
		if user is not None:
			return UserMessage(userid=user.key.integer_id(), password=user.password)
		else:
			user = User(password=pwd.mkpassword(),
				registered_token=TokenModel(source=request.source, key=request.key, secret=request.secret))
			user_key = user.put()
		return UserMessage(userid=user_key.integer_id(), password=user.password)

	SOURCES_METHOD_RESOURCE = endpoints.ResourceContainer(Token, userid=messages.IntegerField(2, required=True))

	@endpoints.method(SOURCES_METHOD_RESOURCE, EmptyMessage,
						path='users/{userid}/sources', http_method='POST', name='postSources')
	def post_sources(self, request):
		basic_auth = self.request_state.headers.get('authorization')
		logging.info("basic oauth : " + str(basic_auth))
		logging.info("request.userid : " + str(request.userid))
		user = User.get_by_id(request.userid)
		logging.info("user's passwo " + str(user.password))
		if user is None:
			raise endpoints.BadRequestException("No such user")
		elif user.password != basic_auth:
			raise endpoints.BadRequestException("Invalid password")
		# sources = []
		user.tokens.append(TokenModel(source=request.source, key=request.key, secret=request.secret))
		logging.info(user.put().integer_id())
		return EmptyMessage()

	NEWS_METHOD_RESOURCE = endpoints.ResourceContainer(count=messages.IntegerField(1, default=15),
	 								offset=messages.IntegerField(2, default=0), userid=messages.IntegerField(3, required=True))

	@endpoints.method(NEWS_METHOD_RESOURCE, NewsCollection,
						path='users/{userid}/news', http_method='GET', name='getNews')
	def get_news(self, request):
		module.TwitterModule()
		basic_auth = self.request_state.headers.get('authorization')
		user = User.get_by_id(request.userid)
		if user is None:
			raise endpoints.BadRequestException("No such user")
		elif user.password != basic_auth:
			raise endpoints.BadRequestException("Invalid password")
		factory = module.ModuleFactory()
		feed = []
		items = []
		for token in user.tokens:
			items.extend(factory.get_news(token.source, (token.key, token.secret), request.count, request.offset))
		items = sorted(items, key=itemgetter('time'), reverse=True)[:request.count]
		for news in items:
			feed.append(News(source=news['source'], content=news['content']))
		return NewsCollection(feed=feed)

APPLICATION = endpoints.api_server([UsersApi])





