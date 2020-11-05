import xmlModelParser

def groundAutoTypesInTarget(target, world):
	# Make sure the world model provided is a graph (not the path to it)
	if type(world) == str:
		world = xmlModelParser.graphFromXMLFile(world)
	# Iterate over the target's graph, grounding the auto symbols according to the types of the init world model
	for node in target["graph"].nodes:
		if target["graph"].nodes[node].sType == "auto":
			try:
				useless_justToForceExceptions = int(target["graph"].nodes[node].name) # If the node is not a constant, we should fail
				for nodeCheck in world.nodes:
					if node == nodeCheck:
						target["graph"].nodes[node].sType = world.nodes[nodeCheck].sType
			except ValueError: # Ok, if the node is not a constant, we should fail
				print 'Found an \'auto\' symbol type for a symbol which is not a constant'
				sys.exit(-1)
