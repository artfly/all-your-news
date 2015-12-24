from abc import ABCMeta, abstractmethod
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb


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
	refresh_token = ndb.StringProperty()
	access_token = ndb.StringProperty()


class BaseModuleApi(remote.Service):

	SOURCES_METHOD_RESOURCE = endpoints.ResourceContainer(Token, userid=messages.IntegerField(2, required=True))
	NEWS_METHOD_RESOURCE = endpoints.ResourceContainer(
			userid=messages.IntegerField(1, required=True), count=messages.IntegerField(2, required=True),
															since=messages.IntegerField(3, required=True))

	def post_token(self, request):
		raise NotImplementedError("Stub!")

	def get_news(self, request):
		raise NotImplementedError("Stub!")