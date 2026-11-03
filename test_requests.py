import requests
resp = requests.get('https://en.wikipedia.org/wiki/KRI_Nagapasa')
print(resp.status_code)
