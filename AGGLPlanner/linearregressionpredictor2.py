import copy
import pickle
import numpy as np
from operator import itemgetter

from parseAGGL import AGMFileDataParsing

from genericprediction import *


class LinearRegressionPredictor2(object):
	def __init__(self, pickleFile):
		try:
			f = open(pickleFile, 'r')
		except IOError:
			print ('agglplanner error: Could not open', pickleFile)
		# print str.split(' ', 1 )
		self.coeff, self.intercept, self.xHeaders, self.yHeaders = pickle.load(f)
		self.coeff = np.array(self.coeff)
		self.intercept = np.array(self.intercept)
		print ('--------------------------------------------------------------------')
		self.prdDictionary = setInverseDictionaryFromList(self.xHeaders)
		self.actDictionary = setInverseDictionaryFromList(self.yHeaders)


	def get_distrb(self, init_types, init_binary, init_unary, initModel, targetVariables_types, targetVariables_binary, targetVariables_unary, target): # returns data size time
		inputv = inputVectorFromTargetAndInit(self.domainParsed, self.prdDictionary, self.actDictionary, target, initModel)
		outputv = np.dot(inputv, self.coeff)+self.intercept

		result = copy.deepcopy(self.actDictionary)
		for key in self.actDictionary:
			value = self.actDictionary[key]
			result[key] = outputv[0][value]

		kk = sorted([ [x, result[x] ] for x in result ], reverse=True, key=itemgetter(1))
		indexes = []
		thresholds = [0.5, 0.125, 0.0]
		for idx, action in enumerate(sorted([ [x, result[x] ] for x in result ], reverse=True, key=itemgetter(1))):
			if action[1] < thresholds[0]:
				if idx != 0:
					indexes.append(idx)
				thresholds = thresholds[1:]
				if len(thresholds) == 0:
					break
		#print 'indexes', indexes
		chunkSize = []
		for idx in reversed(indexes):
			#print 'idx', idx
			if len(chunkSize) > 0:
				#print 'hay cosas ya', chunkSize[-1], idx
				if abs(chunkSize[-1]-idx)>1:
					#print 'condicion'
					chunkSize.append(idx)
			else:
				#print 'no habia nada'
				chunkSize.append(idx)

		chunkSize = [ float(x)/(len(self.actDictionary)-1) for x in reversed(chunkSize)]
		if chunkSize[-1] < 0.999999:
			chunkSize.append(1)

		chunkTime = []
		timeSplitter = 4.
		for x in chunkSize:
			chunkTime.append(timeSplitter)
			timeSplitter *= 0.5
		return result, chunkSize, chunkTime


def generateLinearRegressionMatricesFromDomainAndPlansDirectory2(domain, data, outX, outY):
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
			planPDDL   = target   + '.plan.plan.pddl'
			if x.endswith('.aggt'):
				# print 'x', x
				# print os.path.exists(plan), os.path.exists(target)
				for plan in [planE, planPDDL]:
					if os.path.exists(plan) and os.path.exists(target):
						# print 'x1'
						if os.path.getsize(plan)>15:
							# print 'x2'
							planLines = [x.strip().strip('*') for x in open(plan, 'r').readlines() if (not x.startswith('#')) and len(x) > 3 ]
							try:
								if plan.endswith('pddl'):
									yi = outputVectorFromPDDLPlan(planLines, actDictionary, factor=0.5)
								elif plan.endswith('plan2'):
									yi = outputVectorFromPlan(planLines, actDictionary, factor=0.5)
								else:
									print ('plan which is not .pddl or .plan')
									sys.exit(-3)
							except KeyError:
								print ('Non existent action in', plan)
								continue
							try:
								data_y = np.concatenate( (data_y, yi), axis=0)
							except NameError:
								data_y = yi # traceback.print_exc()
							xi = np.zeros( (1, 2*len(prdDictionary)) )
							initWorld = plan.split('/')[:-1]
							initWorld.append(initWorld[-1]+'.xml')
							initWorld = '/'.join(initWorld)
							# print initWorld
							# sys.exit(-1)
							xi = inputVectorFromTargetAndInit(domainAGM, prdDictionary, actDictionary, target, initWorld)
							try:
								try:
									data_x = np.concatenate( (data_x, xi), axis=0)
								except NameError:
									data_x = xi # traceback.print_exc()
								n += 1
								if n%100 == 0:
									print (n, 'generateLinearRegressionMatricesFromDomainAndPlansDirectory2')
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
