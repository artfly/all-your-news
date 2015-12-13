import logging
from google.appengine.api import urlfetch
import json
import endpoints

class ModuleFactory:
	class __ModuleFactory:
		def __init__(self):
			pass
		def __str__(self):
			return repr(self)
	instance = None
	modules = {'twitter' : 'https://ayn-module-twitter.appspot.com', 'reddit' : 'https://ayn-module-reddit.appspot.com'}
	def __init__(self):
		if not ModuleFactory.instance:
			ModuleFactory.instance = ModuleFactory.__ModuleFactory()


	def get_news(self, source, userid, count, offset):
		logging.info(source)
		if source in self.modules.keys():
			url = self.modules[source] + '/_ah/api/module/v1/users/{}/news?count={}'.format(userid, count)
			content = json.loads(urlfetch.fetch(url=url, method=urlfetch.GET).content)
			# logging.info(str(content))
			try:
				feed = content['feed']
			except KeyError:
				raise endpoints.BadRequestException(content['error']['message'])
			return content['feed']


	def post_token(self, source, token, userid):
		if source in self.modules.keys():
			url = self.modules[source] + '/_ah/api/module/v1/users/{}/tokens'.format(userid)
			payload = {'token' : token}
			# logging.info(str(payload))
			headers = {'Content-Type': 'application/json'}
			urlfetch.fetch(url=url, payload=json.dumps(payload), method=urlfetch.POST,headers=headers)


	# def post_offset(self, source, userid, offset):				#TODO
