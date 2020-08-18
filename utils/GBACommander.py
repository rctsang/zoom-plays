import time
from utils.keys import Keyboard
### Node Class ###
# Class for implementing an substring search tree
class Node:

	def __init__(self, val=None, wordEnd=False):
		self.wordEnd = wordEnd
		self.val = val
		self.keys = set()
		self.children = dict()

	def addChildNode(self, val, wordEnd=False):
		if val and val not in self.keys:
			self.keys.add(val)
			self.children[val] = Node(val, wordEnd)
			return self.children[val]

	def childless(self):
		return self.keys == False

	def __repr__(self):
		if self:
			return '[' + str(self.val) + ', ' + str(self.wordEnd) + ']'
		else:
			return ""

	def printTree(self, lvl=0):
		if not self.childless():
			print('\t' * lvl + repr(self))
			for key in self.keys:
				self.children[key].printTree(lvl+1)

class GBACommand:
	cmdMap = {
		'up'		: 'up',
		'down'		: 'down',
		'left'		: 'left',
		'right'		: 'right',
		'u'			: 'up',
		'd'			: 'down',
		'l'			: 'left',
		'r'			: 'right',
		'start'		: '\n',
		'select'	: 'rshift',
		'a'			: 'x',
		'b'			: 'z',
		'ltrig'		: 'a',
		'rtrig'		: 's',
		'lt'		: 'a',
		'rt'		: 's',
		'killswitch': None,
	}
	pressOnly = {'start', 'select', 'killswitch'}
	kb = None

	def __init__(self, press=None, hold=None, mul=1):
		if not self.kb:
			self.kb = Keyboard()
		self.press = press
		self.hold = hold
		self.mul = mul
		if hold in self.pressOnly:
			self.hold = None
		if press in self.pressOnly:
			self.mul = 1

	def __repr__(self):
		val = ""
		if self.hold: 
			if self.press:
				val += str(self.hold) + '+'
			else:
				val += '!' + str(self.hold)
		if self.press:
			val += str(self.press)
		if self.mul > 1:
			val += '*' + str(self.mul)
		return val

	def empty(self):
		return (not self.press) and (not self.hold)

	def execute(self):
		if self.press == 'killswitch':
			print("we ded")
			return 1

		if self.hold:
			self.kb.KeyDown(self.cmdMap[self.hold])
		
		if self.press and self.mul > 0 and self.mul <= 500:
			for i in range(self.mul):
				if i > 0:
					time.sleep(0.025)
				self.kb.KeyDown(self.cmdMap[self.press])
				time.sleep(0.175)
				self.kb.KeyUp(self.cmdMap[self.press])

		if not self.press and self.mul < 5:
			time.sleep(self.mul)

		if self.hold:
			self.kb.KeyUp(self.cmdMap[self.hold])

		print(self)
		time.sleep(0.05)


class CommandFinder:
	nums = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

	def addWord(self, node, word):
		if node:
			if len(word) > 1:	# Recursive Case
				if word[0] not in node.keys:
					self.addWord(node.addChildNode(word[0]), word[1:])
				else:
					self.addWord(node.children[word[0]], word[1:])
			elif word in node.keys:	# Base Case 1: last letter is already a child
				node.children[word].wordEnd = True
				# Add '+' and '*' nodes here if necessary with a can Hold bool
			else:	# Base Case is not yet a child
				node.addChildNode(word, True)	

	def __init__(self, commands=None, pressOnly=None):
		self.root = Node()
		# self.root.addChildNode('+')
		# self.root.addChildNode('*')
		# self.plus = self.root.children['+']
		# self.mul = self.root.children['*']

		if not commands:
			commands = GBACommand.cmdMap.keys()
			pressOnly = GBACommand.pressOnly
		for cmd in commands:
			self.addWord(self.root, cmd)
		# for key in self.root.keys if key not in pressOnly:
		# 	self.plus.children[key] = self.root.children[key]

	def printFinder(self):
		self.root.printTree()

	### Function to return all instances of each command in the string, including duplicates
	# NOTE: the word must be spelled correctly, with whitespace before and after it (' ' or '\n')
	# 		if it is to be identified properly
	# Returns a list of commands with items in the format [[vals], #]
	def find(self, string):
		string = string.lower()
		val = ""
		cmd = GBACommand()
		cmds = []
		head = self.root
		for i in range(len(string)):
			# print(char, end = "")
			val += string[i]
			if string[i] in head.keys:	# Current char is part of a valid cmd string
				head = head.children[string[i]]
				if head.wordEnd:	# Current Char is the last char of a valid cmd 
					if (i+1 >= len(string) or string[i+1] == ' ' or string[i+1] == '\n'):
						# Current Command is a Single Press Button
						# print(val)
						cmd.press = val
						cmds += [cmd]
					elif string[i+1] == '+':
						# Current Command is a Combo Hold Button
						# print(val)
						cmd.hold = val
						# print(cmd)
					elif string[i+1] == '*':
						# Current Command is a Multiple Press Button
						# print(val)
						cmd.press = val
						# print(cmd)
					elif string[i+1] == '!':
						# Current Command is a Hold Button
						cmd.hold = val
			elif string[i] in self.nums and (cmd.press or cmd.hold):	# Current char is a number with associated cmd
				if (i+1 >= len(string)) or string[i+1] == ' ' or string[i+1] == '\n':
					# Command sequence ended correctly
					# Found Multiplier
					# print(val)
					cmd.mul = int(val)
					cmds += [cmd]
			else:
				if not cmd.empty() and string[i] not in {'+', '*', '!'}:
					cmd = GBACommand()
				val = ""
				head = self.root
				
				
			
		return cmds


##### Some Testing Stuff #####
# testString = "b+down*10\nu*10\nl*5\nb+r*25\nleft*2"
# testString = "gobbldeegook"
# # cmds = ['up', 'down', 'left', 'right', 'ltrigger', 'rtrigger', 'a', 'b', 'l']


# finder = CommandFinder(GBACommand.cmdMap.keys())
# finder.printFinder()

# gbacmds = finder.find(testString)

# for cmd in gbacmds:
# 	print(repr(cmd) + ", ", end="")
# print("\n")

