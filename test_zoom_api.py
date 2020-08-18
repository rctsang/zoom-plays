import json
import time
import requests
import http.server
import socketserver
import webbrowser
import multiprocessing
from multiprocessing import Value, Pipe
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from base64 import urlsafe_b64encode

### GLOBALS ###
# !!! Remember to change this here and in Zoom Marketplace if you restarted ngrok server
REDIRECT_URI = "https://7da5afeb38c4.ngrok.io"
AUTHORIZE_URL = "https://zoom.us/oauth/authorize"
ACCESS_TOKEN_URL = "https://zoom.us/oauth/token"
parent_conn, child_conn = Pipe()

class RedirectHandler(SimpleHTTPRequestHandler):

	def __init__(self, *args, directory=None, **kwargs):
		super().__init__(*args, directory=None, **kwargs)
		self.close_connection = True

	def do_GET(self):
		"""Serve a GET request."""
		query = urlparse(self.path).query
		if query:
			qs = parse_qs(query)
			global child_conn
			auth_code = qs['code'][0]
			print("auth code: " + auth_code)
			child_conn.send(auth_code)
			f = self.send_head()
		if f:
			try:
				self.copyfile(f, self.wfile)
			finally:
				f.close()

server_running = Value('i', 0)
Handler = RedirectHandler

def run_server(conn):
	PORT = 8080
	global Handler

	with socketserver.TCPServer(("", PORT), Handler) as httpd:
		print("serving at port", PORT)
		global server_running
		server_running.value = 1
		httpd.handle_request()
		conn.close()

# Save credentials (used for saving refresh token mostly)
def write_creds(creds):
	with open('private/creds.json', 'w', encoding='utf-8') as creds_json:
		json.dump(creds, creds_json, ensure_ascii=False, indent=4)

# Refreshes Oauth2 Access Tokens if Refresh Token is valid
def refresh_access_tokens(creds, tokens):
	val = creds['client_id'] + ':' + creds['client_secret']
	val = "Basic" + urlsafe_b64encode(val.encode('ascii')).decode('utf-8')
	headers = {'Authorization': val}

	global ACCESS_TOKEN_URL
	if 'refresh_token' in creds:
		response = requests.post(
			ACCESS_TOKEN_URL,
			headers=headers,
			data={
				'grant_type': 'refresh_token',
				'refresh_token': creds['refresh_token']
			}
		)
		if int(response.status_code) != 200:
			print("Unable to Refresh Access Token!")
			creds.pop('refresh_token', None)
			write_creds(creds)
			return False

		jsonresponse = response.json()

		creds['refresh_token'] = jsonresponse['refresh_token']
		write_creds(creds)

		for key in jsonresponse.keys():
			tokens[key] = jsonresponse[key]

		return tokens

	else: 
		return False

# Gets Oauth2 Access and Refresh Tokens if Authorized
def get_access_tokens(creds, tokens):
	if 'refresh_token' in creds:
		oauth_tokens = refresh_access_tokens(creds, tokens)
		if oauth_tokens:
			return oauth_tokens

	global ACCESS_TOKEN_URL
	global REDIRECT_URI
	response = requests.post(
		ACCESS_TOKEN_URL,
		data={
			'grant_type': 'authorization_code',
			'code': creds['auth_code'],
			'client_id': creds['client_id'],
			'client_secret': creds['client_secret'],
			'redirect_uri': REDIRECT_URI
		}
	)
	
	oauth_tokens = response.json()

	if int(response.status_code) != 200:
		print(oauth_tokens)
		print("Authentication failed. Exiting...")
		creds.pop('auth_code', None)
		write_creds(creds)
		exit()

	creds['refresh_token'] = oauth_tokens['refresh_token']
	write_creds(creds)

	for key in oauth_tokens.keys():
		tokens[key] = oauth_tokens[key]

		return tokens

	return oauth_tokens

# Wrapper for Zoom Get Chat Channels API
def get_channels(creds, tokens):
	GET_CHANNELS_URL = "https://api.zoom.us/v2/chat/users/me/channels"

	headers = {'authorization': "Bearer " + tokens['access_token']}

	response = requests.get(
		GET_CHANNELS_URL,
		headers=headers,
		params={
			'page_size': 10
		}
	)
	if int(response.status_code) != 200:
		print("API Call Failed! Exiting...")
		exit()

	jsonresponse = response.json()

	time.sleep(1)

	if 'channels' in jsonresponse.keys():
		if jsonresponse['channels']:
			return jsonresponse['channels']
		print("User has no chat channels! Exiting...")
	exit()

# Wrapper for Zoom Get User Chat Messages API
def get_chat_messages(creds, tokens, to_contact="", to_channel="", date="", page_size=50, next_page_token=""):
	GET_CHAT_MESSAGES_URL = "https://api.zoom.us/v2/chat/users/me/messages"

	headers = {'authorization': "Bearer " + tokens['access_token']}
	data = {}
	if to_contact:
		data['to_contact']
	print(to_channel)

	response = requests.get(
		GET_CHAT_MESSAGES_URL,
		headers=headers,
		params={
			'to_channel': to_channel,
			'page_size': page_size,
		}
	)

	time.sleep(1)
	return response.json()



def main():
	with open('private/creds.json', 'r') as creds_json:
		creds = json.load(creds_json)

	CLIENT_ID = creds['client_id']
	CLIENT_SECRET = creds['client_secret']

	global REDIRECT_URI
	global AUTHORIZE_URL
	global ACCESS_TOKEN_URL

	# if we do not have an authorization code, get one and save it to cred.json
	if 'auth_code' not in creds.keys():
		qdict = {'response_type': 'code', 
				 'client_id': CLIENT_ID,
				 'client_secret': CLIENT_SECRET,
				 'redirect_uri': REDIRECT_URI}
		install_url = AUTHORIZE_URL + '?' + urlencode(qdict)

		p = multiprocessing.Process(target=run_server, args=(child_conn,))
		p.start()

		while not server_running.value:
			print("waiting for server...")
			time.sleep(0.01)

		webbrowser.open(install_url)

		auth_code = parent_conn.recv()
		p.join()

		if not auth_code:
			print("Error: No Authorization Code Received!")
			return

		print("auth code: " + auth_code)

		creds['auth_code'] = auth_code

		write_creds(creds)

	print("Authorized! Code: " + creds['auth_code'])

	oauth_tokens = {}

	print("Aquiring Access Tokens...")
	get_access_tokens(creds, oauth_tokens)
	print("Aquired Access Tokens!")
	print("Access Token: " + oauth_tokens['access_token'])

	input("pause")
	print("Getting Channels...")
	channels = get_channels(creds, oauth_tokens)
	print("Channels Aquired!")

	print("Channels:")
	for c in channels:
		print(c['name'])
	print("\n")

	# Uncomment this to select chat channel on startup
	# channel_name = input("Select Chat Channel to Access: ")
	channel_name = "zoomplays test channel"
	channel = {}

	for c in channels:
		if channel_name == c['name']:
			channel = c
			
	if not channel:
		print("Could not find Channel \"" + channel_name + "\". Exiting...")
		exit()

	print('\"' + channel_name + "\" found! Channel ID: " + channel['id'])

	# usually would pass page token too
	print("getting chat messages from channel \"" + channel_name + "\"...")
	response = get_chat_messages(creds, oauth_tokens, to_channel=channel['id'])

	if 'code' in response.keys():
		if int(response['code']) == 124:
			print("access token expired, refreshing access token...")
			oauth_tokens = refresh_access_tokens(creds, tokens)
			if oauth_tokens:
				print("access tokens refreshed, continuing...")
		elif int(response['code']) != 200:
			print(response)
			print("unable to get chat messages from \"" + channel_name + "\". Exiting...")
			exit()

	messages = response['messages']

	for message in messages:
		print(message['message'])


main()


