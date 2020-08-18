
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

	def addWord(self, word):

		if self and len(word) > 1:
			if word[0] not in self.keys:
				self.addChildNode(word[0]).addWord(word[1:])
			else:
				self.children[word[0]].addWord(word[1:])
		elif self and word in self.keys:
			self.children[word].wordEnd = True
		elif self:
			self.addChildNode(word, True)

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


class SubStringFinder:

	def __init__(self, commands : list):
		self.root = Node()
		for cmd in commands:
			self.root.addWord(cmd)

	def printFinder(self):
		self.root.printTree()

	### Function to return all instances of each word in the string, including duplicates
	# NOTE: the word must be spelled correctly, with whitespace before and after it (' ' or '\n')
	# 		if it is to be identified properly
	def find(self, string):
		cmd = ""
		cmds = []
		head = self.root
		for i in range(len(string)):
			# print(char, end = "")
			cmd += string[i]
			if string[i] in head.keys:
				head = head.children[string[i]]
				if i+1 < len(string) and head.wordEnd and (string[i+1] == ' ' or string[i+1] == '\n'):
					cmds += [cmd]
				elif i+1 >= len(string):
					cmds += [cmd]
			else:
				cmd = ""
				head = self.root
				
			
		return cmds


##### Some Testing Stuff #####
# testString = "upp left right \n down up ltrigger \nup aup lebft l "
# cmds = ['up', 'down', 'left', 'right', 'ltrigger', 'rtrigger', 'a', 'b']

# finder = SubStringFinder(cmds)
# finder.printFinder()

# print(finder.find(testString))


