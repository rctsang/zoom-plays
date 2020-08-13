import sys
import time
import numpy as np 
from PIL import ImageGrab
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from textblob import TextBlob
from keys import Keyboard
from search import SubStringFinder

# This is the main execution file of the ZoomPlays application

cmdMap = {
	'up'		: 'up',
	'down'		: 'down',
	'left'		: 'left',
	'right'		: 'right',
	'start'		: '\n',
	'select'	: 'rshift',
	'a'			: 'x',
	'b'			: 'z',
	'l'			: 'a',
	'r'			: 's',
	'KILLSWITCH': False
}

def countdown(t):
	for i in range(t):
		print("*** %d ***\r" %(t-i), end="")
		time.sleep(1)
	print('\r')

kb = Keyboard()

transcript = ""
binarize = lambda x : 255 if x > 100 else 0

# This function finds the substring of newstring that was appended onto string and returns the substring
# This function only looks at the end of string, ignoring any differences at the beginning
def getNewText(string, newstring):
	i = -1
	j = -1
	newTextStart = 0
	matchedChars = 0
	while (abs(i) <= len(string) and abs(j) <= len(string) and matchedChars < 30):
		if string[i] == newstring[j]:
			i -= 1
			j -= 1
			matchedChars += 1
		else:
			newTextStart = j
			j -= 1

	return newstring[newTextStart:]


##### MAIN #####

cmdfinder = SubStringFinder(cmdMap.keys())

args = sys.argv
logName = "log.txt"

if len(args) > 1:
	logName = args[1]

print("\n\n\nGET READY.")
time.sleep(1)
print('\r', end="")

countdown(3)

# start main loop
live = True
with open("chatlogs/" + logName, 'w') as logfile:
	while (input("\nENTER to continue...") == ""):
		countdown(2)

		# the chatbox is usually 300x640
		screen = ImageGrab.grab(bbox=(10, 50, 360, 1000))
		screen = screen.convert('L')

		# Minor Image Processing for dark mode screens
		screen = ImageOps.invert(screen)
		# screen = screen.point(binarize, mode='1')

		screen.save('test_imgs/grabbed.png')

		# Start Tesseract OCR
		text = pytesseract.image_to_string(screen)
		# print("\nraw----------\n")
		# print(text)

		# determine the new text that has appeared in the chatbox
		newText = getNewText(transcript, text)
		print("\nnewtext------\n")
		print(newText)

		# keep a log of all messages so far in a separate txt file
		logfile.writelines(newText)
		transcript += newText

		# keep the last 30 chars of the transcript so we can know when we've seen something before
		if (len(transcript) > 30):
			transcript = transcript[-30:]
		print("\ntranscript---\n")
		print(transcript)

		# get the command inputs from the new text
		cmds = cmdfinder.find(newText)

		# send command to game via key event
		for cmd in cmds:
			if cmd == 'KILLSWITCH':
				live = False
				break;
			print(cmd)
			kb.KeyDown(cmdMap[cmd])
			time.sleep(0.1)
			kb.KeyUp(cmdMap[cmd])
			time.sleep(0.01)

		# time.sleep(2)