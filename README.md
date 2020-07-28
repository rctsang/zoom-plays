# Zoom Plays

This is my attempt to emulate a "twitch plays"-like game but on the conference call platform Zoom.
This is my first time using using a web API so I'll be using this readme to document the dev process. I loosely followed the tutorial outlined [here](https://medium.com/swlh/how-i-automate-my-church-organisations-zoom-meeting-attendance-reporting-with-python-419dfe7da58c) by billydharmawan. Since I want to access the Zoom chat, I need to use Oauth 2.0 instead of JWT though.

**Roadmap with no detail whatsoever:**
1. Somehow extract commands from the messages in the chat log real time
1. Use commands to trigger key-events emulated by x360ce xbox controller emulator
1. Open a game emulator initialized to xbox controller for gameplay

Strictly speaking, using the xbox controller is unnecessary. 


Also, I attempted to use pipenv at first, but ran into some issues, so pipenv can be ignored for now.

## Text from In-Meeting Chat
Ok so in-meeting chat is different from regular chat and cannot easily be accessed. rip that idea.
(closest thing apparently is to use Zoom WebSDK and access chat features and message log through sessionStorage, but I have 0 experience with web dev)

## OCR Version Notes

So instead let's see if we can take live screen-captures of the in-meeting chat log and try to extract the commands from that.

So we're using tesseract and pytesseract as our OCR library/software, and Pillow in order to take screenshots using ImageGrab, which means that this program is only gonna work on Windows and Mac OS.

Using this [stackoverflow post](https://stackoverflow.com/questions/54795273/live-screen-monitoring-with-python3-pytesseract) as inspiration, I've written a test script called `test_tesseract.py` which is a manual loop that takes screenshots of the zoom in-meeting chatbox, determines what new text has appeared on the screen, and prints it, saving the whole chat log to a .txt file separately. 

Tesseract is very good at OCR if the image is black and white, low noise, and the image is black text on white background, which means some image pre-processing is necessary for it to work well on applications with dark mode enabled.

**Step-by-Step Process**
1. Screenshot chatbox area
1. Convert image to greyscale
1. Invert image if chatbox had dark mode active
1. Binarize image to black and white
1. image-to-text using Tesseract

**ALAS, this didn't work as well as I hoped...**
There's no trouble pulling the text, but it's very difficult to determine what commands have already been logged, so the OCR method is unfortunately untenable.

Guess it's either YouTube live stream or Zoom Chats...
For now I will attempt to use the YouTube API in in a different repo

## Game Interface Notes

I originally decided to use OpenEmu as a game emulator to test this, but alas, OpenEmu does not support AppleScript, which means that key events generated by conventional python libraries are useless since OpenEmu registers key events at a lower level (i.e. non of my generated keystrokes are registered by OpenEmu).

I have 3 options:
1. I can attempt to build a virtual HID (Human Interface Device) that generates key events at a low enough level for OpenEmu to register it (see [cython-hidapi](https://pypi.org/project/hidapi/0.7.99.post14/))
1. I can try to pipe OSC commands to HID using [Osculator](http://www.osculator.net/) as suggested on the OpenEmu issue [thread](https://github.com/OpenEmu/OpenEmu/issues/1169)
1. I can try another emulator.

Let's go with #3 for now.

I've selected mGBA (which OpenEmu uses as it's GBA core) as an emulator and that seems to work, though there are some minor bugs in the emulator.


In seeing other examples of live plays, apparently Lua Scripting is a common way to hack a GBA emulator, which would be an idea way to send controls to the emulator, but unfortunately, most emulators compatible with macOS lack luascripting capabilities. There's only one known emulator that might have the capability, but it's outdated. See links for lua for more details. 


### Requirements

- pipenv==2020.6.2 (maybe?)

**For OCR:**
- pillow
- tessaract==4.0
- pytesseract
- opencv-python
- textblob

**For Game Interface:**
- pyobjc-framework-quartz

### Useful Links

- [pipenv](https://docs.python-guide.org/dev/virtualenvs/)
- [Zoom - Using OAuth 2.0](https://marketplace.zoom.us/docs/guides/auth/oauth)
- [Zoom Git - OAuth Sample App](https://github.com/zoom/zoom-oauth-sample-app)
- [Zoom Forum - creating meeting oauth in python](https://devforum.zoom.us/t/creating-meeting-oauth-in-python-3-7/20821)
- [Zoom Forum - allow chatbots to join in-meeting chats](https://devforum.zoom.us/t/allow-chatbots-to-join-meeting-chats/8875/19)
- [Zoom - Creating Zoom SDK app](https://marketplace.zoom.us/docs/guides/build/sdk-app)
- [Zoom - WebSDK github](https://github.com/zoom/websdk)
- [Zoom - Marketplace](https://marketplace.zoom.us/)
- [OAuth 2.0 Framework](https://tools.ietf.org/html/rfc6749)
- [OAuth Step by Step](http://www.lexev.org/en/2015/oauth-step-step/)
- [ZoomForum - understanding OAuth for Zoom](https://devforum.zoom.us/t/understanding-oauth-for-zoom/12444)
- [OAuth2 Simplified](https://aaronparecki.com/oauth-2-simplified/)
- [Python Twitch Stream Tutorial](https://317070.github.io/python/)
- [TwitchPlays.py](https://www.dougdougw.com/twitch-plays-code/twitchplays-py)
- [TwitchPlaysX github](https://github.com/hzoo/TwitchPlaysX)
- [make your own twitch plays](https://www.wituz.com/make-your-own-twitch-plays-stream.html)
- [Twitch plays pokemon clone](https://github.com/aidanrwt/twitch-plays)
- [zoom api python wrapper](https://github.com/prschmid/zoomus)

**For OCR**
- [Taking Screenshots with OpenCV and Python](https://www.pyimagesearch.com/2018/01/01/taking-screenshots-with-opencv-and-python/)
- [TextBlob Documentation](https://textblob.readthedocs.io/en/dev/)
- [OpenCV OCR and text recognition with Tesseract](https://www.pyimagesearch.com/2018/09/17/opencv-ocr-and-text-recognition-with-tesseract/)
- [Installing Tesseract for OCR](https://www.pyimagesearch.com/2017/07/03/installing-tesseract-for-ocr/)
- [Installing OpenCV](https://stackoverflow.com/questions/51853018/how-do-i-install-opencv-using-pip)
- [OCR on inage with text in different colors](https://stackoverflow.com/questions/61134400/pytesseract-ocr-on-image-with-text-in-different-colors)

**For Game Interface**
- [Mac Virtual Keycodes](https://gist.github.com/eegrok/949034)
- [Generating Keyboard Events in Python (stackoverflow)](https://stackoverflow.com/questions/13564851/how-to-generate-keyboard-events-in-python)
- [apple developer quartz event services](https://developer.apple.com/documentation/coregraphics/quartz_event_services#//apple_ref/c/func/CGEventCreateKeyboardEvent)
- [quartz to generate key events](https://stackoverflow.com/questions/6868167/how-to-generate-keyboard-keypress-events-through-python-to-control-pp-presentati)
- [CGEventCreateKeyboardEvent](https://developer.apple.com/documentation/coregraphics/1456564-cgeventcreatekeyboardevent?language=objc)
- [PyPI Quartz page](https://pypi.org/project/pyobjc-framework-Quartz/)

- [hidapi github](https://github.com/libusb/hidapi)
- [cython homepage](https://cython.org/#about)

- [TASVideos Emulator Resources](http://tasvideos.org/EmulatorResources/VBA/LuaScriptingFunctions.html)
- [Github TASVideos/vba-rerecording](https://github.com/TASVideos/vba-rerecording)
- [SDL used by vbe-rr](http://www.libsdl.org/)
- [Lua Scripting Example with an SNES emulator on Windows](https://www.twilio.com/blog/2015/08/romram-hacking-building-an-sms-powered-game-genie-with-lua-and-python.html)
- [Lua Homepage](https://www.lua.org/)
- [Lua Manual](https://www.lua.org/manual/5.4/manual.html#2)
- [Python Wrapper Package for Lua](https://pypi.org/project/lupa/)