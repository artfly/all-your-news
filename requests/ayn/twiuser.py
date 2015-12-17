import requests
import json
import sys


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("usage : {} <is_local>")
		sys.exit(1)
	if int(sys.argv[1]) != 0:
		url = 'http://localhost:8080/_ah/api/ayn/v1/users'
	else:
		url = 'https://all-your-news.appspot.com/_ah/api/ayn/v1/users'
	payload = {'token' : "{'token_key' : '3748392675-6ea3Kf58iIebwp0ZWBLjrXcbINd7zWaxSb3HbSn', 'token_secret' : 'GXYsdCYTDTZPeSDITBKV9TrC476sV2ivZ5zIEBF2heNJr'}", 'source' : "twitter"}
	headers = {'Content-Type' : 'application/json'}
	r = requests.post(url, headers=headers, data=json.dumps(payload))
	data = json.loads(r.content.decode())
	print('{} {} {}'.format(data['userid'], data['password'], sys.argv[1]))