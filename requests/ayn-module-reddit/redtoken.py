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
		url = 'https://ayn-module-reddit.com/_ah/api/module/v1/users/5555/tokens'
	payload = {'token' : "{'access_token' : '44847841-R2BMxtnTvmdbkAaCMAJRSrfhO7M', 'refresh_token' : '44847841-st26_A_T53ZO3G8catPt4JRiUuE'}"}
	headers = {'Content-Type' : 'application/json'}
	r = requests.post(url, headers=headers, data=json.dumps(payload))
	if r.status_code == 200:
		print('ok')
	else:
		print("error : status code is {}".format(r.status_code))