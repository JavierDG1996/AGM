#!/usr/bin/env python

# -*- coding: utf-8 -*-
#
#  -------------------------
#  -----  AGGLPlanner  -----
#  -------------------------
#
#  Almost a free/libre AI planner.
#
#  Copyright (C) 2013 by Luis J. Manso
#
#  AGGLPlanner is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  AGGLPlanner is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with AGGLPlanner. If not, see <http://www.gnu.org/licenses/>.




#---------------------------------------------------------------------------------------------------------------------------------------------------#
"""@package agglplan
    @ingroup PyAPI
    This file loads the grammar, the initial state of the world and the GOAL status without changing the files extensions of the grammar and the goal.

    MODE USE:	agglplan2 grammar.aggl init.xml target.aggt learning.data

    Also, we can keep the results in a file with: agglplan grammar.aggl init.xml target.xml learning.data result.plan
"""

# Python distribution imports
import sys, traceback, subprocess

sys.path.append('/usr/local/share/agm/')
from AGGL import *
from parseAGGL import *
from generateAGGLPlannerCode import *
from agglplanner2 import *
from agglplanchecker import *
# from generate import Generate
import agglplanner2_utils



if __name__ == '__main__': # program domain problem result
	def find_arg(l, v):
		for idx, value in enumerate(l):
			if v == value:
				return l[idx+1]
		return None
	def showHelp():
		print ('Usage\n\t', sys.argv[0], 'domain.aggl init.xml target.aggt [-o result.plan] [-l learning_algorithm[:data_file]]\n')
		print ('-l    The learning algorithm can be one of the following (case insensitive): None, NaiveBayes, DummySemantics, LinearRegression, DNN.')
		print ('      If no learning method is provided agglplan used "None" as default option.\n')
		print ('-o    Optional file path to store the computed plan. Optional argument.\n')
		print ('')
		sys.exit(-1)
	# We check if the program was run with all necessary arguments.
	# If there aren't all the arguments, we show an error mesage with how to use the program.
	# If there are all the arguments, we keep them in local variables.
	if len(sys.argv)<4:
		showHelp()
	else:
		## the file that contains the grammar rules
		domainFile = sys.argv[1]
		## the file that contains the initial world status
		worldFile  = sys.argv[2]
		## the goal o target world status
		targetFile = sys.argv[3]
		try:
			## the file name where we keep the results of the program
			result = find_arg(sys.argv, '-o')
		except:
			showHelp()
		try:
			## probability distribution generator
			trainFile = find_arg(sys.argv, '-l')
			if trainFile == None: trainFile = 'none'
		except:
			showHelp()
		trainList = trainFile.split(':')
		trainMethod = trainList[0].lower()
		print ('trainMethod', trainMethod)
		validMethods = [ 'none', 'naivebayes', 'dummysemantics', 'linearregression', 'dnn' ]
		if not trainMethod in validMethods:
			print ('ERROR:', trainMethod, 'not in the list of known learning methods: None, NaiveBayes, DummySemantics, LinearRegression, DNN\n')
			showHelp()
		trainList2 = [trainList[0].lower()]
		if len(trainList)>1:
			trainList2 += trainList[1:]
		trainFile = ':'.join(trainList2)
		print ('learning_algorithm:',trainFile)
		print ('\nGenerating search code...')
		## Generate domain Python file <--- like aggl2agglpy.
		# agmData is a variable of AGMFileData class, in AGGL.py file.
		# First: we CHECK the grammar. Is a parseAGGL.py's class
		# and we write the grammar in a python file.
		agmData = AGMFileDataParsing.fromFile(domainFile)
		agmData.generateAGGLPlannerCode("/tmp/domain.py", skipPassiveRules=True)

		## Generate target Python file.
		if targetFile.lower().endswith('.aggt'):
			theTarget = AGMFileDataParsing.targetFromFile(targetFile)
			agglplanner2_utils.groundAutoTypesInTarget(theTarget, worldFile) 
			outputText = generateTarget_AGGT(agmData, theTarget)
		else:
			# This sentence creates a graph based on the target world status
			graph = graphFromXMLFile(targetFile)
			## Generate the python code correspondig to the graph and
			outputText = generateTarget(graph)
		## Save the python code of the target world status in the file target.py.
		ofile = open("/tmp/target.py", 'w')
		ofile.write(outputText)
		ofile.close()

		# Run planner
		import time
		print ('done\nRunning the planner...')
		## We store the initial or start time of the planner and call the agglplaner, the main program that makes all the process...
		start = time.time()


		print ('RESULT', result)
		print ('TRAINN', trainFile)

		if result:
			subprocess.call(["agglplanner2", domainFile, "/tmp/domain.py", worldFile, "/tmp/target.py", trainFile, result])
		else:
			subprocess.call(["agglplanner2", domainFile, "/tmp/domain.py", worldFile, "/tmp/target.py", trainFile])
		## We store the final time of the planner to calculate the total duration of the program
		end = time.time()
		print ('It took', end - start, 'seconds')
