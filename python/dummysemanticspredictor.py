from parseAGGL import AGMFileDataParsing
import copy

class DummySemanticsPredictor(object):
	def __init__(self, parsed):
		self.types = {}
		self.predicates = {}
		self.parsed = copy.deepcopy(parsed)
		for rule in self.parsed.agm.rules:
			self.types[rule.name] = set()
			self.predicates[rule.name] = set()
			for graph in [ rule.lhs, rule.rhs ]:
				for node in graph.nodes:
					self.types[rule.name].add(graph.nodes[node].sType)
				for link in graph.links:
					self.predicates[rule.name].add(link.linkType)
		# print 'TYPES:', self.types
		# print 'PREDS:', self.predicates
	def get_distrb(self, init_types, init_binary, init_unary, initModel, targetVariables_types, targetVariables_binary, targetVariables_unary): # returns data size time
		needTypes = set(targetVariables_types) #- set(init_types)
		# print '\n\n'
		# print 'init_types:', init_types
		# print 'targetVariables_types:', targetVariables_types
		# print 'needTypes:', needTypes

		# print 'iu', init_unary
		# print 'ib', init_binary
		# print 'tu', targetVariables_unary
		# print 'tb', targetVariables_binary
		# needPreds = set([p[0] for p in targetVariables_binary | targetVariables_unary | init_binary | init_unary])
		needPreds = set([p for p in targetVariables_binary | targetVariables_unary | init_binary | init_unary])
		# print '\n\n'
		# print 'init_binary:', init_binary
		# print 'targetVariables_binary:', targetVariables_binary
		# print 'needPreds:', needPreds

		result = {}
		for rule in self.parsed.agm.rules:
			# if rule.name != 'setObjectReach':
				# continue
			result[rule.name] = 0
			ruleTypes = set()
			rulePredsL = set()
			# for preds, graph in [(rulePredsL, rule.lhs), (rulePredsR, rule.rhs)]
			for node in rule.lhs.nodes:
				typeA = rule.lhs.nodes[node].sType
				for tA in [typeA] + self.parsed.agm.inverseTypes[typeA]:
					ruleTypes.add(tA)
			for link in rule.lhs.links:
				lt = link.linkType
				if not link.enabled: lt += '*'
				typeA = rule.lhs.nodes[link.a].sType
				for tA in [typeA] + self.parsed.agm.inverseTypes[typeA]:
					if link.a != link.b:
						typeB = rule.lhs.nodes[link.b].sType
						for tB in [typeB] + self.parsed.agm.inverseTypes[typeB]:
							rulePredsL.add((lt, tA, tB))
					else:
						rulePredsL.add((lt, tA))
			rulePredsR = set()
			for node in rule.rhs.nodes:
				typeA = rule.rhs.nodes[node].sType
				for tA in [typeA] + self.parsed.agm.inverseTypes[typeA]:
					ruleTypes.add(tA)
			for link in rule.rhs.links:
				lt = link.linkType
				if not link.enabled: lt += '*'
				typeA = rule.rhs.nodes[link.a].sType
				for tA in [typeA] + self.parsed.agm.inverseTypes[typeA]:
					if link.a != link.b:
						typeB = rule.rhs.nodes[link.b].sType
						for tB in [typeB] + self.parsed.agm.inverseTypes[typeB]:
							rulePredsR.add((lt, tA, tB))
					else:
						rulePredsR.add((lt, tA))

			# print ''
			# print 'rulePredsL', rulePredsL
			# print 'rulePredsR', rulePredsR
			pointsByTypes = len( ruleTypes & needTypes )
			pointsByPredsRequired = len( rulePredsL & needPreds )
			pointsByPredsAdded    = len( (rulePredsR-rulePredsL) & needPreds )
			points = 0.125*pointsByTypes+0.5*pointsByPredsRequired+2.0*pointsByPredsAdded
			# print 'points for', rule.name, points
			result[rule.name] = points
			# print '  types:', pointsByTypes
			# print '  predR:', pointsByPredsRequired, rulePredsL & needPreds
			# print '  predA:', pointsByPredsAdded, rulePredsR & needPreds

		chunkSize = [0.3, 0.7, 0.9, 1.0]
		chunkTime = [ 2.,  2.,  2.,  2.]

		return result, chunkSize, chunkTime

#
