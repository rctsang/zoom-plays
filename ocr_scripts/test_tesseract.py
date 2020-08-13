import numpy as np 
from PIL import ImageGrab
import pytesseract
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from textblob import TextBlob

# This is a test file for real time chat message reading in Zoom using OCR

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

with open('test_chatlogs/log.txt', 'w') as logfile:
	while (input("\nENTER to continue...") == ""):

		# the chatbox is usually 300x640
		screen = ImageGrab.grab(bbox=(1560,90,1860,730))
		screen = screen.convert('L')

		# Minor Image Processing for dark mode screens
		screen = ImageOps.invert(screen)
		screen = screen.point(binarize, mode='1')

		screen.save('test_imgs/grabbed.png')

		# Start Tesseract OCR
		text = pytesseract.image_to_string(screen)
		# print("\nraw----------\n")
		# print(text)

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

		# correctedText = TextBlob(text).correct()
		# print("corrected----")
		# print(correctedText)