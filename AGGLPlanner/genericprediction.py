import sys, random, os, traceback
from subprocess import call
import numpy as np
import imp
import pickle, copy

import xmlModelParser
import agglplanner2_utils

sys.path.append('/usr/local/share/agm/')
from parseAGGL import AGMFileDataParsing
from generateAGGLPlannerCode import generateTarget_AGGT


def getActionDictionary(domain):
	ret = {}
	count = 0
	#print '<<getActionDictionary'
	for rule in domain.agm.rules:
		#print rule.name
		ret[rule.name] = count
		count += 1
	#print '>>getActionDictionary'
	return ret


def outputVectorFromPlan(planLines, actionDictionary, factor=1.):
	F = 1.
	ret = np.zeros( (1, len(actionDictionary)) )
	#try:
	for line in planLines:
		actionName  = line.split('@')[0]
		actionIndex = actionDictionary[actionName]
		ret[0][actionIndex] = F
		F *= factor
	#except KeyError:
		#print planLines
	return ret

def outputVectorFromPDDLPlan(planLines, actionDictionary, factor=1.):
	F = 1.
	ret = np.zeros( (1, len(actionDictionary)) )
	#try:
	for line in planLines:
		if len(line) > 0:
			if line[0] != ';' and line[0] != '#':
				actionName  = line[1:].split()[0]
				try:
					actionIndex = actionDictionary[actionName]
				except (KeyError, e):
					try:
						for k in actionDictionary.keys():
							if actionName == k.lower():
								actionName = k
						actionIndex = actionDictionary[actionName]
					except (KeyError, e):
						print ('Non existent action in plann: ', actionName)
						print ('-------------')
						for xx in actionDictionary.keys():
							print ('x', xx)
						print ('-------------')
						sys.exit(1)
				ret[0][actionIndex] = F
				F *= factor
	#except KeyError:
		#print planLines
	return ret


def getPredicateDictionary(domain):
	predicates = set()
	for rule in domain.agm.rules:
		for link in rule.rhs.links:
			if not link in rule.lhs.links:
				lt = link.linkType
				if not link.enabled: lt += '*'
				binary =  link.a == link.b
				typeA = rule.rhs.nodes[link.a].sType
				for tA in domain.agm.inverseTypes[typeA]:
					typeB = rule.rhs.nodes[link.b].sType
					for tB in domain.agm.inverseTypes[typeB]:
						if not (binary and tA!=tB):
							predicates.add((lt, tA, tB))
	ret = {}
	count = 0
	for p in predicates:
		s = '#'.join(p)
		ret[s] = count
		count += 1
	return ret

def setInverseDictionaryFromList(lst):
	ret = {}
	for i, item in enumerate(lst):
		ret[item] = i
	return ret

# def inputVectorFromSets(domain, prdDictionary, actDictionary, init_types, init_binary, init_unary, initModel, targetVariables_types, targetVariables_binary, targetVariables_unary):
# 	a, b, c = targetVariables_types, targetVariables_binary, targetVariables_unary
# 	print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
# 	print a
# 	print b
# 	print c
# 	print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
# 	print prdDictionary
# 	print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
# 	ret = np.zeros( (1, len(prdDictionary)) )
# 	for r in b|c:
# 		if len(r) == 2:
# 			x = (r[0], r[1], r[1])
# 		elif len(r) == 3:
# 			x = r
# 		else:
# 			print 'inputVectorFromTarget: unexpected predicate size', r
# 			sys.exit(-1)
# 		k = '#'.join(x)
# 		if k in prdDictionary.keys():
# 			print prdDictionary[k], ret.shape
# 			ret[0][prdDictionary[k]] = 1
# 	return ret

def inputVectorFromTarget(domain, prdDictionary, actDictionary, target, initWorld):
	# Auto symbols must be grounded before computing the input vector
	if type(initWorld) == str:
		initWorld = xmlModelParser.graphFromXMLText(initWorld)

	if type(target) == type(''):
		parsedTarget = AGMFileDataParsing.targetFromText(target)
		agglplanner2_utils.groundAutoTypesInTarget(parsedTarget, initWorld)
		code = generateTarget_AGGT(domain, parsedTarget)
		m = imp.new_module('targetModule')
		exec (code in m.__dict__)
		a, b, c = m.getTargetVariables()
		ret = np.zeros( (1, len(prdDictionary)) )
		for r in b|c:
			if len(r) == 2:
				x = (r[0], r[1], r[1])
			elif len(r) == 3:
				x = r
			else:
				print ('inputVectorFromTarget: unexpected predicate size', r)
				sys.exit(-1)
			k = '#'.join(x)
			if k in prdDictionary.keys():
				# print prdDictionary[k], ret.shape
				ret[0][prdDictionary[k]] = 0
		return ret

	else:
		print ('to implement (maybe we are in a hierarchical target which is given directly by code)')
		sys.exit(-1)


def inputVectorFromTargetAndInit(domain, prdDictionary, actDictionary, target, initWorld):
	if type(initWorld) == str:
		if initWorld.startswith('<'):
			initWorld = xmlModelParser.graphFromXMLText(initWorld)
		else:
			initWorld = xmlModelParser.graphFromXMLFile(initWorld)

	# Fill vector with the predicates from the target
	if type(target) == type(''):
		if target.endswith('.aggt'):
			parsedTarget = AGMFileDataParsing.targetFromFile(target)
		else:
			parsedTarget = AGMFileDataParsing.targetFromText(target)
		# Auto symbols must be grounded before computing the input vector
		agglplanner2_utils.groundAutoTypesInTarget(parsedTarget, initWorld)
		code = generateTarget_AGGT(domain, parsedTarget)
		m = imp.new_module('targetModule')
		exec (code in m.__dict__)
		a, b, c = m.getTargetVariables()
		ret = np.zeros( (1, 2*len(prdDictionary)) )
		for r in b|c:
			if len(r) == 2:
				x = (r[0], r[1], r[1])
			elif len(r) == 3:
				x = r
			else:
				print ('inputVectorFromTarget: unexpected predicate size', r)
				sys.exit(-1)
			k = '#'.join(x)
			if k in prdDictionary.keys():
				ret[0][prdDictionary[k]] = 1
	else:
		print ('to implement (maybe we are in a hierarchical target which is given directly by code)')
		sys.exit(-1)

	for edge in initWorld.links:
		if edge.a in parsedTarget["graph"].nodes and edge.b in parsedTarget["graph"].nodes:
			k = edge.linkType + '#' + initWorld.nodes[edge.a].sType + '#' + initWorld.nodes[edge.b].sType
			try:
				ret[0][len(prdDictionary)+prdDictionary[k]] = 1
				# print k
			except:
				pass

	return ret


class LinearRegressionHeuristic(object):
	def __init__(self, pickleFile):
		try:
			f = open(pickleFile, 'r')
		except IOError:
			print ('agglplanner error: Could not open', pickleFile)
		self.coeff, self.intercept, self.xHeaders, self.yHeaders = pickle.load(f)
		self.coeff = np.array(self.coeff)
		self.intercept = np.array(self.intercept)
		self.prdDictionary = setInverseDictionaryFromList(self.xHeaders)
		self.actDictionary = setInverseDictionaryFromList(self.yHeaders)
	def get_heuristic(self, init_types, init_binary, init_unary, initModel, targetVariables_types, targetVariables_binary, targetVariables_unary, target): # returns data size time
		inputv = inputVectorFromTargetAndInit(self.domainParsed, self.prdDictionary, self.actDictionary, target, initModel)
		outputv = np.dot(inputv, self.coeff)+self.intercept
		return 100.*outputv[0][0]



from chainer import Variable
# from chainer import datasets, iterators, optimizers, serializers
from chainer import Link, Chain, ChainList
# from chainer.datasets import tuple_dataset
import chainer.functions as F
import chainer.links as L

class DNNHeuristic(object):
	def __init__(self, pickleFile):
		try:
			with open(pickleFile, 'r') as ff:
				self.model, self.xHeaders, self.yHeaders = pickle.load(ff)
		except IOError:
			print ('agglplanner error: Could not open', pickleFile)
		self.prdDictionary = setInverseDictionaryFromList(self.xHeaders)
		self.actDictionary = setInverseDictionaryFromList(self.yHeaders)
	def get_heuristic(self, init_types, init_binary, init_unary, initModel, targetVariables_types, targetVariables_binary, targetVariables_unary, target): # returns data size time
		inputv = inputVectorFromTargetAndInit(self.domainParsed, self.prdDictionary, self.actDictionary, target, initModel)
		outputv = self.model.predict(Variable(inputv.astype(np.float32))).array[0][0]
		# print outputv
		return 100.*outputv



#   generateHeuristicMatricesFromDomainAndPlansDirectory(domain, data, "xHeuristicData.csv", "yHeuristicData.csv")
def generateHeuristicMatricesFromDomainAndPlansDirectory(domain, data, outX, outY):
	print ('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Reading domain')
	domainAGM = AGMFileDataParsing.fromFile(domain)

	print ('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Generating prdsHeader')
	prdDictionary = getPredicateDictionary(domainAGM)
	prdsHeader=range(len(prdDictionary))
	for x in prdDictionary:
		prdsHeader[prdDictionary[x]] = x
	print (prdsHeader)


	print ('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Generating actsHeader')
	actDictionary = getActionDictionary(domainAGM)
	actsHeader=range(len(actDictionary))
	for x in actDictionary:
		actsHeader[actDictionary[x]] = x
	print (actsHeader)


	print ('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Gathering data from stored files')
	lim = -1
	n = 0
	for (dirpath, dirnames, filenames) in os.walk(data):
		for x in filenames:
			target = dirpath  +   '/'   + x
			planE   = target   + '.plane'
			plan2   = target   + '.plan2'
			planPDDL   = target   + '.plan.plan.pddl'
			if x.endswith('.aggt'):
				# print 'x', x
				# print os.path.exists(plan), os.path.exists(target)
				for plan in [planE, plan2, planPDDL]:
					if os.path.exists(plan) and os.path.exists(target):
						# print 'x1'
						if os.path.getsize(plan)>15:
							# print 'x2'
							planLines = [x.strip().strip('*') for x in open(plan, 'r').readlines() if (not x.startswith('#')) and len(x) > 3 ]
							yi = np.zeros( (1, 1) )
							yi[0][0] = float(len(planLines))
							try:
								data_y = np.concatenate( (data_y, yi), axis=0)
							except NameError:
								data_y = yi # traceback.print_exc()
							xi = np.zeros( (1, 2*len(prdDictionary)) )
							initWorld = plan.split('/')[:-1]
							initWorld.append(initWorld[-1]+'.xml')
							initWorld = '/'.join(initWorld)
							xi = inputVectorFromTargetAndInit(domainAGM, prdDictionary, actDictionary, target, initWorld)
							try:
								try:
									data_x = np.concatenate( (data_x, xi), axis=0)
								except NameError:
									data_x = xi # traceback.print_exc()
								n += 1
								if n%100 == 0:
									print (n, 'generateHeuristicMatricesFromDomainAndPlansDirectory')
								if n == lim:
									print ('wiiiiiiiiiii')
									break
							except KeyError:
								print ('KeyError _ ', plan)
								traceback.print_exc()
			if n == lim:
				break
		if n == lim:
			break

	print ('x', np.sum(data_x))
	print (data_x.shape)
	# print data_x

	print ('y', np.sum(data_y))
	print (data_y.shape)
	# print data_y


	with open(outY, 'wb') as f:
		f.write(';'.join(actsHeader)+'\n')
		np.savetxt(f, data_y, delimiter=";")

	with open(outX, 'wb') as f:
		f.write(';'.join(prdsHeader)+'\n')
		np.savetxt(f, data_x, delimiter=";")


#
