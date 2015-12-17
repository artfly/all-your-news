import requests
import json
import sys


if __name__ == '__main__':
	if len(sys.argv) != 4:
		print("usage : {} <userid> <password> <is_local>")
		sys.exit(1)
	if int(sys.argv[3]) != 0:
		url = 'http://localhost:8080/_ah/api/ayn/v1/users'
	else:
		url = 'https://all-your-news.appspot.com/_ah/api/ayn/v1/users/{}/sources'.format(sys.argv[1])
	payload = {'token' : "{'token_key' : '3748392675-6ea3Kf58iIebwp0ZWBLjrXcbINd7zWaxSb3HbSn', 'token_secret' : 'GXYsdCYTDTZPeSDITBKV9TrC476sV2ivZ5zIEBF2heNJr'}", 'source' : "twitter"}
	headers = {'Authorization' : sys.argv[2], 'Content-Type' : 'application/json'}
	r = requests.post(url, headers=headers, data=json.dumps(payload))
	if r.status_code == 200:
		print(' '.join((sys.argv[1:])))
	else:
		print("error : status code is {}".format(r.status_code))