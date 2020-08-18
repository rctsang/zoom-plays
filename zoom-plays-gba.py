import os
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
from utils.keys import Keyboard
from utils.GBACommander import *

### GLOBALS ###
# !!! Remember to change this here and in Zoom Marketplace if you restarted ngrok server
REDIRECT_URI = "https://7da5afeb38c4.ngrok.io"
AUTHORIZE_URL = "https://zoom.us/oauth/authorize"
ACCESS_TOKEN_URL = "https://zoom.us/oauth/token"
parent_conn, child_conn = Pipe()
DIRECTORY = "server"

# HTTP request handler class
class RedirectHandler(SimpleHTTPRequestHandler):

	def __init__(self, *args, directory=None, **kwargs):
		super().__init__(*args, directory=DIRECTORY, **kwargs)
		self.close_connection = True

	def do_GET(self):
		"""
		Serve a GET request.
		Meant to operate in a separate process. Passes extracted code to the main process
		"""
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

# semaphore to check if server up
server_running = Value('i', 0)
Handler = RedirectHandler

# run server method to be called in a separate process
def run_server(conn):
	PORT = 8080
	global Handler

	# start a new TCP server with HTTP request handler
	with socketserver.TCPServer(("", PORT), Handler) as httpd:
		print("serving at port", PORT)
		global server_running
		server_running.value = 1
		httpd.handle_request() 		# server handles one request, then terminates
		conn.close()				# terminate the end of the pipe passed to the process

# Simple countdown display
def countdown(t):
    for i in range(t):
        print("\r*** %d ***" %(t-i), end="")
        time.sleep(1)
    print("\r*** 0 ***")

# Save credentials (used for saving refresh token mostly)
def write_creds(creds):
	with open('private/creds.json', 'w', encoding='utf-8') as creds_json:
		json.dump(creds, creds_json, ensure_ascii=False, indent=4)

# REFRESH ACCESS TOKENS
# Refreshes Oauth2 Access Tokens if Refresh Token is valid
def refresh_access_tokens(creds, tokens):

	# Construct the Refresh Token Request Header expected by the api
	val = creds['client_id'] + ':' + creds['client_secret']
	# api expects client id and secret Byte64 encoded
	val = "Basic" + urlsafe_b64encode(val.encode('ascii')).decode('utf-8') 
	headers = {'Authorization': val}

	global ACCESS_TOKEN_URL
	if 'refresh_token' in creds:
		# if the refresh token exists, sent a POST request to the Zoom access token url
		# with the headers and expecter query parameters
		response = requests.post(
			ACCESS_TOKEN_URL,
			headers=headers,
			data={
				'grant_type': 'refresh_token',
				'refresh_token': creds['refresh_token']
			}
		)

		# Error Checking - if the refresh failed, return false so new access tokens can be requested
		if int(response.status_code) != 200:
			print("Unable to Refresh Access Token!")
			creds.pop('refresh_token', None)
			write_creds(creds)
			return False

		# requests can turn the byte response into a dictionary
		jsonresponse = response.json()

		# write the new refresh token to memory for next time
		creds['refresh_token'] = jsonresponse['refresh_token']
		write_creds(creds)

		# overwrite the expired tokens with the new tokens
		for key in jsonresponse.keys():
			tokens[key] = jsonresponse[key]

		return tokens

	else: 
		return False

# GET ACCESS TOKENS
# Gets Oauth2 Access and Refresh Tokens if Authorized
# overwrites the token parameter dictionary with the new tokens
def get_access_tokens(creds, tokens):

	# if there is an available refresh token, attempt to refresh
	# if the refresh succeeds, return, otherwise continue to request new tokens
	if 'refresh_token' in creds:
		oauth_tokens = refresh_access_tokens(creds, tokens)
		if oauth_tokens:
			return oauth_tokens

	global ACCESS_TOKEN_URL
	global REDIRECT_URI
	# POST request for new access and refresh tokens using OAuth Code
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
	
	# get dictionary of response
	oauth_tokens = response.json()

	# error checking, if there was a fail, remove the refresh token from memory if present and exit
	if int(response.status_code) != 200:
		print(oauth_tokens)
		print("Authentication failed. Exiting...")
		creds.pop('auth_code', None)
		write_creds(creds)
		exit()

	# write new refresh token to memory
	creds['refresh_token'] = oauth_tokens['refresh_token']
	write_creds(creds)

	# write or overwrite the deprecated tokens dictionary
	for key in oauth_tokens.keys():
		tokens[key] = oauth_tokens[key]

		return tokens

	return tokens

# GET CHANNELS
# Wrapper for Zoom Get Chat Channels API
# returns a list of dictionaries containing channel information
def get_channels(creds, tokens):
	GET_CHANNELS_URL = "https://api.zoom.us/v2/chat/users/me/channels"

	# HTTP Request header with valid access token 
	headers = {'authorization': "Bearer " + tokens['access_token']}

	# GET request for User's active Chat Channels
	response = requests.get(
		GET_CHANNELS_URL,
		headers=headers,
		params={
			'page_size': 10
		}
	)

	# error checking
	if int(response.status_code) != 200:
		print("API Call Failed! Exiting...")
		exit() # if failed, exit to evaluate problem

	jsonresponse = response.json()

	# rate limit for basic Zoom users is 1 request/second
	time.sleep(1)

	# return all the user's active chat channels, exit program otherwise
	if 'channels' in jsonresponse.keys():
		if jsonresponse['channels']:
			return jsonresponse['channels']
		print("User has no chat channels! Exiting...")
	exit()

# GET CHAT MESSAGES
# Wrapper for Zoom Get User Chat Messages API
# returns the result of the API call WITHOUT ERROR CHECKING
# Return Example Format:
# {
#   "date": "2020-08-17",
#   "messages": [
#     {
#       "date_time": "2020-08-17T21:24:19Z",
#       "id": "DAE33F9D-3B12-42F6-AE72-0475A49CDB42",
#       "message": "test",
#       "sender": "sender@example.com",
#       "timestamp": 1597699459794
#     }
#   ],
#   "next_page_token": "",
#   "page_size": 10
# }
def get_chat_messages(creds, tokens, to_contact="", to_channel="", date="", page_size=50, next_page_token=""):
	GET_CHAT_MESSAGES_URL = "https://api.zoom.us/v2/chat/users/me/messages"

	# authorization header
	headers = {'authorization': "Bearer " + tokens['access_token']}
	
	# construct the url query dictionary
	params = {}
	if to_contact:
		params['to_contact'] = to_contact
	elif to_channel:
		params['to_channel'] = to_channel
	if date:
		params['date'] = date
	params['page_size'] = page_size
	if next_page_token:
		params['next_page_token'] = next_page_token

	# GET request for next set of messages from user
	response = requests.get(
		GET_CHAT_MESSAGES_URL,
		headers=headers,
		params=params
	)

	# rate limit considerations
	time.sleep(1)
	return response.json()



def main():
	# initialize keyboard to generate key events
	# kb = Keyboard()

	# initialize the CommandFinder for GBA Commands
	finder = CommandFinder(GBACommand.cmdMap.keys())

	# load client credentials from file
	with open('private/creds.json', 'r') as creds_json:
		creds = json.load(creds_json)

	CLIENT_ID = creds['client_id']
	CLIENT_SECRET = creds['client_secret']

	global REDIRECT_URI
	global AUTHORIZE_URL
	global ACCESS_TOKEN_URL

	# if we do not have an authorization code, get one and save it to cred.json
	if 'auth_code' not in creds.keys():

		# construct query dictionary for the authorization url
		qdict = {'response_type': 'code', 
				 'client_id': CLIENT_ID,
				 'client_secret': CLIENT_SECRET,
				 'redirect_uri': REDIRECT_URI}
		# append url query to base authorization url
		install_url = AUTHORIZE_URL + '?' + urlencode(qdict)

		# start a separate process to run http server that will wait for authentication
		p = multiprocessing.Process(target=run_server, args=(child_conn,))
		p.start()

		# make sure not to make server requests before it's ready
		while not server_running.value:
			print("waiting for server to start...")
			time.sleep(0.01)

		# open the authentication page in a browser window
		# user will allow app access to his/her chat channels and messages
		webbrowser.open(install_url)

		# wait for the server's handler to send the authentication code to the main process via pipe
		auth_code = parent_conn.recv()

		# once server process is completed, join it with the main process
		p.join()

		# make sure the authorization code was received
		if not auth_code:
			print("Error: No Authorization Code Received!")
			return

		# write authoriation code to file
		creds['auth_code'] = auth_code
		write_creds(creds)

	print("Authorized! Code: " + creds['auth_code'])

	# initialize an empty access tokens dictionary
	oauth_tokens = {}

	print("Aquiring Access Tokens...")
	get_access_tokens(creds, oauth_tokens)
	print("Aquired Access Tokens!")
	print("Access Token: " + oauth_tokens['access_token'])

	print("Getting Channels...")
	channels = get_channels(creds, oauth_tokens)
	print("Channels Aquired!")

	# display all found chat channels
	print("Channels:")
	for c in channels:
		print(c['name'])
	print("")

	# Uncomment this to select chat channel on startup
	# channel_name = input("Select Chat Channel to Access: ")
	channel_name = "zoomplays test channel"
	
	# initialize dictionary for active channel
	channel = {}

	# select desired chat channel to access
	for c in channels:
		if channel_name == c['name']:
			channel = c
	
	# error checking
	if not channel:
		print("Could not find Channel \"" + channel_name + "\". Exiting...")
		exit()
	print('\"' + channel_name + "\" found! Channel ID: " + channel['id'])

	if input("Ready? (y/n) ") in ['n', 'no']:
		print("Aborting...")
		exit()
	print("Starting connection...")
	countdown(3) 	# Wait for user to pull up gba emulator for keystroke input

	# Begin looping to access tokens

	alive = True
	# next_page_token = ""
	last_message_id = ""
	cnt = 0
	while(alive):

		# get chat messages from channel
		print("getting chat messages from channel \"" + channel_name + "\"...")
		response = get_chat_messages(creds, oauth_tokens, to_channel=channel['id'])

		# error checking, if access token expired, refresh it
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

		""
		# next_page_token = response['next_page_token']

		# get message dictionaries from response
		messages = response['messages']

		# messages are stored in order of most recent first and next_page_token doesn't tell us there we left off
		# so we need to search down the message list until we hit a message that we've seen before (they all have unique ids)

		if last_message_id: # if it's the first get, ignore all past messages
			# first, we'll loop through messages and add each message to a stack until we get to the last seen message
			cmd_stack = []
			for message in messages:
				if message['id'] == last_message_id:
					# stop if we've seen this message already
					break
				cmd_stack.append(message['message'])

			# then execute the commands from the stack in chronological order		
			while cmd_stack:
				cmds = finder.find(cmd_stack.pop())
				for cmd in cmds:
					# the cmd is a GBACommand object that can self execute, normally void method
					# if the command is a killswitch, execute() returns 1
					if cmd.execute():
						exit()


		# Finally, save the id of the last message seen
		last_message_id = messages[0]['id']


main()


