import requests
import json
import sys


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("usage : {} <is_local>".format(sys.argv[0]))
		sys.exit(1)
	if int(sys.argv[1]) != 0:
		url = 'http://localhost:8080/_ah/api/module/v1/users/5555/tokens'
	else:
		url = 'https://ayn-module-twitter.com/_ah/api/module/v1/users/5555/tokens'
	payload = {'token' : "{'token_key' : '3748392675-6ea3Kf58iIebwp0ZWBLjrXcbINd7zWaxSb3HbSn', 'token_secret' : 'GXYsdCYTDTZPeSDITBKV9TrC476sV2ivZ5zIEBF2heNJr'}"}
	headers = {'Content-Type' : 'application/json'}
	r = requests.post(url, headers=headers, data=json.dumps(payload))
	if r.status_code == 200:
		print('ok')
	else:
		print("error : status code is {}".format(r.status_code))