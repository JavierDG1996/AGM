import copy, sys


##@brief This class manages the exception of a wrong rule execution.
# It inherits from Excepction.
class WrongRuleExecution(Exception):
	##@brief Constructor method. It saves the data of the Exception
	# @param data anything that gets the information of the Excepction.
	def __init__(self, data):
		## Data of the exception
		self.data = data

	##@brief This method returns the data of the exception.
	# @retval data.
	def __str__(self):
		return self.data


##@brief This class get the name and the parameters of an action that belongs to a plan.
class AGGLPlannerAction(object):
	##@brief Constructor method. It receives (optionally) the contructor method of the object, but, by default, it is empty.
	# @param init is the plan
	# If anything is wrong, this method throws an exception.
	def __init__(self, init=''):
		object.__init__(self)
		## Name of the rule
		self.name = ''
		## Name of the rule parameters (the parameters are in a dictionary)
		self.parameters = dict()
		if len(init)>0:
			#print 'initializing from:', init
			#we save the the list of all the words in the string, using @ as the separator
			parts = init.split('@')
			self.name = parts[0]
			#print self.name[0], self.name[0] == '*'
			if self.name[0] == '*':
				#print 'hierarchical'
				self.name = self.name[1:]
				self.hierarchical = True
			else:
				self.hierarchical = False
			if not (self.name[0] == '#' and self.name[1] != '!'):
				#print parts[1]
				self.parameters = eval(parts[1])
		else:
			raise IndexError

	##@brief This method returns the name and the parameters of the action in a string.
	# @retval string with the name of the action and the parameters
	def __str__(self):
		if self.hierarchical:
			h = '*'
		else:
			h = ''
		return h+self.name+'@'+str(self.parameters)



## @brief AGGLPlannerPlan is used as a plan container.
class AGGLPlannerPlan(object):
	## @brief Parametrized constructor.
	# @param init is an optional initialization variable. It can be:
	#	a) string containing a plan;
	#	b) a filename where such string is to be found,
	# 	c) a list of tuples where each tuple contains the name of a rule and a dictionary with the variable mapping of the rule.
	# @param planFromText This parameter indicates whether 'init' is the name of a file (where is stored the plan code) or the text string with the plan code. By default his value is FALSE
	def __init__(self, init='', planFromText=False):
		object.__init__(self)

		## Data of the plan file
		self.data = []
		# IF INIT IS A STRING....
		if type(init) == type(''): # Read plan from file (assuming we've got a file path)
			# If init is a string, we check its length. If there are something in the string, we check
			# what it is:
			if len(init)>0:
				 # If the string is all the plan code, we separate in lines with \n, but,
				 # if the string is the name of the file where is stored all the plan code, we read and save
				 # the file content in a local variable.
				if planFromText:
					lines = init.split("\n") #newline
				else:
					lines = open(init, 'r').readlines() # take the content of a file

				# Now, we check the text to find possible errors.
				# First, we delete the white spaces at the start and the end of each text line.
				# Second, we check if there are any line with only the character \n.
				# Finally, is the line have something that is not a commentary, we save it like a grammar rule
				for line_i in range(len(lines)):
					line = lines[line_i].strip() # take a line of the file content
					while len(line)>0:
						if line[-1]=='\n': line = line[:-1]
						else: break
					if len(line)>0:
						if not (line[0] == '#' and line[1] != '!'):
							try:
								a = AGGLPlannerAction(line)
								self.data.append(a)
							except:
								print 'Error reading plan file', init+". Line", str(line_i)+": <<"+line+">>"
			# If the string hasnt got anything, we dont apply any rule:
			else:
				pass
		# IF INIT IS A LIST
		elif type(init) == type([]):
			# we take each element of the list and we save it as a grammar rule.
			for action in init:
				if not (action[0][0] == '#' and action[0][1] != '!'):
					#print type(action), len(action), action
					self.data.append(AGGLPlannerAction(action[0]+'@'+str(action[1])))
		#IF INIT IS A COMPLETE PLAN
		else:
			if init.__class__.__name__ == 'AGGLPlannerPlan':
				# we make a copy of the plan
				self.data = copy.deepcopy(init.data)
			else:
				print 'Unknown plan type ('+str(type(init))+')! (internal error)'
				sys.exit(-321)

	def getAlreadyDecomposedHierarchicalActionNamesList(self):
		ret = []
		for action in self.data:
			n = action.name
			if n.startswith('#!'):
				n = n[2:]
			if n.startswith('*'):
				n = n[1:]
			if not n in ret:
				ret += [n]
		return ret

	## @brief Returns a copy of the plan without the first action assuming the action was executed. It's used for monitorization purposes.
	# @param currentModel Model associated to the current state of the world
	# @retval The resulting version of the plan
	def removeFirstAction(self, currentModel):
		## @internal Create the copy without the first actions.
		c = AGGLPlannerPlan()
		for action in self.data[1:]:
			c.data.append(copy.deepcopy(action))
		## @internal Modify the rest of the actions assuming the first action was executed.
		actionToRemove = self.data[0]
		symbolsInAction = set(actionToRemove.parameters.values())
		nodesInWorld = set(currentModel.nodes.keys())
		created = symbolsInAction.difference(nodesInWorld)
		if len(created) > 0:
			minCreated = min([int(x) for x in created])
			for action in c.data:
				for parameter in action.parameters:
					if int(action.parameters[parameter]) >= minCreated:
						n = str(int(action.parameters[parameter])-len(created))
						action.parameters[parameter] = n
		return c

	def removeFirstActions(self, currentModel, n):
		c = copy.deepcopy(currentModel)
		for i in xrange(n):
			self.removeFirstAction(c)

	def removeFirstActionDirect(self):
		## @internal Create the copy without the first actions.
		c = AGGLPlannerPlan()
		for action in self.data[1:]:
			c.data.append(copy.deepcopy(action))
		return c

	## @brief This method initializes the iterator of the class.
	# @retval the class with the diferent value of the counter
	def __iter__(self):
		## iterator of the data
		self.current = -1
		return self

	## @brief This method counts +1 on the current variable. If the counter overcome the
	# length of the data attribute, it raises an exception. If not, the method returns the
	# data with the index==current+1.
	# @retval the data with the index current+1
	def next(self):
		self.current += 1
		if self.current >= len(self.data):
			raise StopIteration
		else:
			return self.data[self.current]

	##@brief This method returns the information of the graph as a string.
	# @retval a string with the information of the plan graph.
	def __repr__(self):
		## The plan graph
		return self.data.__str__()

	##@brief this method returns a string with the data array information.
	# @retval ret is the string with all the data
	def __str__(self):
		ret = ''
		for a in self.data:
			ret += a.__str__() + '\n'
		return ret

	##@brief this method returns the length of the data array.
	# @retval an integer that is the length of the data array.
	def __len__(self):
		return len(self.data)




##@brief This class saves all the information of the current graph
class WorldStateHistory(object):
	##@brief Constructor method.
	# @param init initialization variable
	def __init__(self, init):
		object.__init__(self)
		# Contains all the actions applied to this state
		self.actionList = []

		# If INIT IS A GRAPH
		if isinstance(init, list):
			# Graph with the current world status.
			self.graph = copy.deepcopy(init[0])
			# The identifier of the graph that the current graph comes from
			self.parentId = 0
			# The cost of the new graph (as result of execute the heuristic?)
			self.cost = 0
			# The string with all the changes made from the original graph.
			self.history = []
			# CostData
			self.costData = []
			# The identifier of the current graph
			self.nodeId = -1
			# Awaken rules set
			self.awakenRules = init[1]
			# The depth of the current graph.
			self.depth = 0
			# A flag to stop.
			self.stop = False
			# The heuristic score of the current graph
			self.score = 0
		#IF INIT IS A INSTANCE OF WorldStateHistory
		elif isinstance(type(init), type(WorldStateHistory)):
			self.graph = copy.deepcopy(init.graph)
			self.cost = copy.deepcopy(init.cost)
			self.awakenRules = copy.deepcopy(init.awakenRules)
			self.costData = copy.deepcopy(init.costData)
			self.history = copy.deepcopy(init.history)
			self.depth = copy.deepcopy(init.depth)
			self.stop = False
			self.score = 0
		else:
			print 'Internal errorr: Cannot create WorldStateHistory from unexpected object of type', str(type(init))
			sys.exit(1)

	##@brief This method compares two graphs.
	# @param other is the graph with which we compare.
	# @retval an integer that can be 1 if the current graph is greater, -1 if it is smaller, and 0 if both are equals.
	def __cmp__(self, other):
		return self.graph.__cmp__(other.graph)

	##@brief This method calculates the hashcode of the current graph.
	# @retval an integer with the hashcode.
	def __hash__(self):
		return self.graph.__hash__()

	##@brief This method returns the result of comparing two graphs
	# @param other the other graph.
	# @retval a boolean wit the result of the comparison
	def __eq__(self, other):
		return self.graph.__eq__(other.graph)

	##@brief This method returns a string with the information of the current graph.
	def __repr__(self):
		return self.graph.__repr__()

	##@brief This method returns a string with the information of the current graph.
	def __str__(self):
		return self.graph.__str__()
