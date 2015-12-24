import endpoints
from protorpc import remote
from ayn_module import BaseModuleApi
import ayn_module
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
import ast
import json
import base64
import logging


module_api = endpoints.api(name='module', version='v1')


class TokenDB(ndb.Model):
	refresh_token = ndb.StringProperty()
	access_token = ndb.StringProperty()


@module_api.api_class(resource_name='users')
class ModuleApi(BaseModuleApi):
	"""Users API v1"""
	CLIENT_ID = 'LFBR3WSQCrOt6g'
	CLIENT_SECRET = 'H35OVobtd4K0YKIl8StDffr4jm0'

	@endpoints.method(BaseModuleApi.SOURCES_METHOD_RESOURCE, ayn_module.EmptyMessage,
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
		return ayn_module.EmptyMessage() 


	def refresh(self, db_token):
		oauth_url = 'https://www.reddit.com/api/v1/access_token'
		payload = 'grant_type=refresh_token&refresh_token={}'.format(db_token.refresh_token)
		headers={"Authorization": "Basic %s" % base64.b64encode("{}:{}".format(self.CLIENT_ID, self.CLIENT_SECRET))}
		new_token = urlfetch.fetch(url=oauth_url, headers=headers,
									method=urlfetch.POST, payload=payload).content
		new_token = json.loads(new_token)
		if 'access_token' in new_token:
			db_token.access_token = new_token['access_token']
			db_token.put()
			return new_token['access_token']
		return None

	@endpoints.method(BaseModuleApi.NEWS_METHOD_RESOURCE, ayn_module.NewsCollection,
						path='users/{userid}/news', http_method='GET', name='getNews')
	def get_news(self, request):
		db_token = TokenDB.get_by_id(request.userid)
		if db_token is None:
			raise endpoints.BadRequestException("No such user")
		count = request.count
		since = request.since
		headers = {"Authorization" : "bearer " + db_token.access_token}
		url = "https://oauth.reddit.com/.json"
		after = ''
		data = []
		params = {}
		taken = 0
		while True:
			url = url + "?limit={}&after={}".format('100', after)
			posts = urlfetch.fetch(url=url, headers=headers, method=urlfetch.GET).content
			posts = json.loads(posts)
			#if request failed
			if 'data' not in posts:
				access_token = self.refresh(db_token)
				if access_token is None:
					break
				headers = {"Authorization" : "bearer " + access_token}
				posts = urlfetch.fetch(url=url, headers=headers, method=urlfetch.GET).content								
				posts = json.loads(posts)

			logging.info(json.dumps(posts))
			for post in posts['data']['children']:
				if taken == count:
					return ayn_module.NewsCollection(feed=data)
				if since > post['data']['created_utc']:
					data.append(ayn_module.News(content=json.dumps(post), time=json.dumps(post['data']['created_utc']), source='reddit'))
					taken += 1
			after = posts['data']['after']
		return ayn_module.NewsCollection(feed=data)


APPLICATION = endpoints.api_server([ModuleApi])