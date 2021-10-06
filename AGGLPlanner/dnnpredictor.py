import copy
import pickle, tempfile
import numpy as np

from parseAGGL import AGMFileDataParsing
# from zipfile import ZipFile

from genericprediction import *

# import chainer
# from chainer import Function, gradient_check, report, training, utils, Variable
from chainer import Variable
# from chainer import datasets, iterators, optimizers, serializers
from chainer import Link, Chain, ChainList
# from chainer.datasets import tuple_dataset
import chainer.functions as F
import chainer.links as L
# from chainer.training import extensions


# def zipFiles(files_paths, output_path):
# 	print 'output_path', output_path
# 	with ZipFile(output_path, 'w') as zip_out:
# 		for f in files_paths:
# 			print f
# 			print zip_out.write(f)


# def getModel(input_path):
# 	zip_base = tempfile.mkdtemp(prefix='agmDNN')
# 	print 'zip_base', zip_base
# 	with ZipFile(input_path, 'r') as zip:
# 		zip.extractall(zip_base)
# 	return zip_base+'/model.h5', zip_base+'/xHeaders.pckl', zip_base+'/yHeaders.pckl'



def generateDNNMatricesFromDomainAndPlansDirectory(domain, data, outX, outY):
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
				for plan in [planE, planPDDL]:
					if os.path.exists(plan) and os.path.exists(target):
						# print 'x1'
						if os.path.getsize(plan)>15:
							# print 'x2'
							planLines = [x.strip().strip('*') for x in open(plan, 'r').readlines() if (not x.startswith('#')) and len(x) > 3 ]
							try:
								if plan.endswith('pddl'):
									yi = outputVectorFromPDDLPlan(planLines, actDictionary, factor=0.5)
								elif plan.endswith('plane'):
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





class MLP(Chain):
	def __init__(self, n_units_a, n_units_b, n_units_c, n_out):
		super(MLP, self).__init__()
		with self.init_scope():
			self.l1 = L.Linear(None, n_units_a)
			self.l2 = L.Linear(None, n_units_b)
			self.l3 = L.Linear(None, n_units_c)
			self.l4 = L.Linear(None, n_out)
	def predict(self, x):
		h1 = F.relu(self.l1(x))
		h2 = F.relu(self.l2(h1))
		h3 = F.relu(self.l3(h2))
		return F.sigmoid(self.l4(h3))
	def __call__(self, x, y):
		predict = self.predict(x)
		loss = F.sum(F.square(predict - y))
		return loss


class MLPSigmoid(Chain):
	def __init__(self, layers):
		super(MLPSigmoid, self).__init__()
		with self.init_scope():
			self.l = []
			for i in layers:
				self.l.append(L.Linear(None, i))
	def predict(self, x):
		out = self.l[0](x)
		for i in self.l[1:-1]:
			out = F.relu(i(copy.deepcopy(out)))
		return F.sigmoid(self.l[-1](out))
	def __call__(self, x, y):
		predict = self.predict(x)
		loss = F.sum(F.square(predict - y))
		return loss




class DNNPredictor(object):
	def __init__(self, inputFile):
		try:
			with open(inputFile, 'r') as ff:
				self.model, self.xHeaders, self.yHeaders = pickle.load(ff)
		except IOError:
			print ('Couldn\'t read', inputFile)
			sys.exit(1)
		print ('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
		print (self.xHeaders)
		print ('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
		print ('--------------------------------------------------------------------')
		self.prdDictionary = setInverseDictionaryFromList(self.xHeaders)
		self.actDictionary = setInverseDictionaryFromList(self.yHeaders)


	def get_distrb(self, init_types, init_binary, init_unary, initModel, targetVariables_types, targetVariables_binary, targetVariables_unary, target): # returns data size time
		inputv = inputVectorFromTargetAndInit(self.domainParsed, self.prdDictionary, self.actDictionary, target, initModel)
		outputv = self.model.predict(Variable(inputv.astype(np.float32))).array
		outputv = outputv - outputv.min()
		outputv = outputv / outputv.max()

		#print '---------------------'
		#print outputv
		#print '<--------------------'

		result = copy.deepcopy(self.actDictionary)
		for key in self.actDictionary:
			value = self.actDictionary[key]
			result[key] = outputv[0][value]
		#print result
		#print '<--------------------'


		from operator import itemgetter
		kk = sorted([ [x, result[x] ] for x in result ], reverse=True, key=itemgetter(1))
		indexes = []
		thresholds = [0.75, 0.25, 0.0]
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

		chunkTime = [ 1 for x in chunkSize ]
		# print result, chunkSize, chunkTime
		return result, chunkSize, chunkTime













#
