import requests
import json
import sys
import time


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("usage : {} <is_local>".format(sys.argv[0]))
		sys.exit(1)
	if int(sys.argv[1]) != 0:
		url = 'http://localhost:8080/_ah/api/module/v1/users/5555/news?count=10&since={}'.format(int(time.time()))
	else:
		url = 'https://ayn-module-twitter.com/_ah/api/module/v1/users/5555/news?count=10&since={}'.format(int(time.time()))
	headers = {'Content-Type' : 'application/json'}
	r = requests.get(url, headers=headers)
	count = 0
	while r.ok is True:
		count += 1
		r = requests.get(url, headers=headers)
	if r.status_code == 200:
		print('ok')
	else:
		print("error : status code is {}, count : {}".format(r.status_code, count))
		print(r.content.decode())