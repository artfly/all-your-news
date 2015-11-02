import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb

package = 'Token'

class DictPickleProperty(ndb.PickleProperty):
    def __init__(self, **kwds):
        kwds['default'] = kwds.get('default', {})
        super(DictPickleProperty, self).__init__(**kwds)


class User(ndb.Model):
	tokens = DictPickleProperty()


class Token(messages.Message):
	token = messages.StringField(1)
	source = messages.StringField(2)


class TokenCollection(messages.Message):
	items = messages.MessageField(Token, 1, repeated=True)


@endpoints.api(name='token', version='v1')
class TokenApi(remote.Service):
	"""TokenApi version1"""

	@endpoints.method(Token, Token,
						path='token', http_method='POST', name='token.postToken')
	def token_post(self, request):
		user = User.get_by_id(request.token)
		if user is not None:
			raise endpoints.BadRequestException("User is already existing")
		else:
			user = User(id=request.token)
			user.put()

		return Token(token=request.token)

	SOURCES_METHOD_RESOURCE = endpoints.ResourceContainer(
		TokenCollection,
		token=messages.StringField(2))

	@endpoints.method(SOURCES_METHOD_RESOURCE, message_types.VoidMessage,
						path='token/{token}', http_method='POST', name='token.addSources')
	def add_sources(self, request):
		user = User.get_by_id(request.token)
		if user is not None:
			for token in request.items:
				user.tokens[token.source] = token.token
			user.put() 
		return message_types.VoidMessage()

	@endpoints.method(endpoints.ResourceContainer(token=messages.StringField(1)), TokenCollection,
													path='token/{token}', http_method='GET', name='token.getSources')
	def get_sources(self, request):
		user = User.get_by_id(request.token)
		if user is not None:
			items = []
			for key, value in user.tokens.iteritems():
				t = Token(token=value, source=key)
				items.append(t)
			return TokenCollection(items=items)

APPLICATION = endpoints.api_server([TokenApi])
