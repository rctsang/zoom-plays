import time
from keys import Keyboard
from search import SubStringFinder

commands = ['a', 'a']

cmdMap = {
	'up'		: 'up',
	'down'		: 'down',
	'left'		: 'left',
	'right'		: 'right',
	'start'		: '\n',
	'select'	: 'rshift',
	'a'			: 'x',
	'b'			: 'z',
	'ltrig'			: 'a',
	'rtrig'			: 's'
}

def countdown(t):
	for i in range(t):
		print("*** %d ***\r" %(t-i), end="")
		time.sleep(1)
	print('\r\n')

# countdown(5)

kb = Keyboard()

# test substring find
# testString = "this is a test string, i'm hoping this finds all instances of the given words"
# keyWords = ["this", "test", "instances"]

cmdfinder = SubStringFinder(cmdMap.keys())

# test substring find commands
testString = "down down left left start b select"

cmds = cmdfinder.find(testString)



# print(found)

countdown(3)
for cmd in cmds:
	print(cmd)
	kb.KeyDown(cmdMap[cmd])
	time.sleep(0.1)
	kb.KeyUp(cmdMap[cmd])
	time.sleep(0.01)

