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
	refresh_token = ndb.StringProperty()
	access_token = ndb.StringProperty()
	offset = ndb.IntegerProperty(default=0)


@module_api.api_class(resource_name='users')
class UsersApi(remote.Service):
	"""Users API v1"""

	SOURCES_METHOD_RESOURCE = endpoints.ResourceContainer(Token, userid=messages.IntegerField(2, required=True))

	@endpoints.method(SOURCES_METHOD_RESOURCE, EmptyMessage,
						path='users/{userid}/tokens', http_method='POST', name='postSource')
	def post_token(self, request):
		token = ast.literal_eval(request.token)
		if 'access_token' in token and 'refresh_token' in token:
			access_token = token['access_token']
			refresh_token = token['refresh_token']
			db_token = TokenDB.get_by_id(request.userid)
			if db_token is None:
				db_token = TokenDB(id=request.userid)
			db_token.access_token = access_token
			db_token.refresh_token = refresh_token
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
		count = request.count
		offset = db_token.offset
		headers = {"Authorization" : "bearer " + db_token.access_token}
		url = "https://oauth.reddit.com/.json"
		# result = urlfetch.fetch(url=url, headers=headers, method=urlfetch.GET)
		# logging.info(result.content)
		# return EmptyMessage()
		lastpost = count + offset - 1
		iterations = int(lastpost / 100) + 1
		after = ''
		data = []
		params = {}
		for i in range(0, iterations):
			url = url + "?limit={}&after={}".format('100', after)
			posts = urlfetch.fetch(url=url, headers=headers, method=urlfetch.GET).content
			# logging.info(posts)
			posts = json.loads(posts)															#TODO : refresh_token
			# posts = self.r.request_json(url='https://oauth.reddit.com/', params={'limit' : '100', 'after' : after})
			if offset < 100 * (i + 1):
				to = (lastpost + 1) if lastpost < 100 else 100
				for j in range(offset % 100, to):
					post = posts['data']['children'][j]
					logging.info(str(post))
					data.append(News(content=str(post), time=str(post['data']['created']), source='reddit'))
				offset = 0
			lastpost -= 100
			after = posts['data']['after']
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