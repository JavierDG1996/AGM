#!/usr/bin/env pypy

# -*- coding: utf-8 -*-
#
#  -------------------------
#  -----  AGGLPlanner  -----
#  -------------------------
#
#  A free/libre open source AI planner.
#
#  Copyright (C) 2013 - 2017 by Luis J. Manso
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
"""@package agglplanner
    @ingroup PyAPI
    This file loads the grammar, the initial state of the world and the GOAL status without changing the files extensions of the grammar and the goal.

    Usage: agglplanner grammar.aggl init.xml target.py trainFile

    Also, we can keep the results in a file with: agglplanner grammar.aggl init.xml target.py trainFile result.plan
"""

import time
#import signal
#import _thread
import threading
import pickle

#signal.signal(signal.SIGINT, signal.SIG_DFL)

import sys, traceback, os, re, threading, string, math, copy
import collections, imp, heapq
import datetime
sys.path.append('/usr/local/share/agm/')

import xmlModelParser
from AGGL import *
import inspect

from generateAGGLPlannerCode import *
from parseAGGL import AGMFileDataParsing
import xmlModelParser
import agglplanchecker
from agglplanchecker import *
from agglplannerplan import *
from generate import *

from dummysemanticspredictor import *
#from linearregressionpredictor import *
#from linearregressionpredictor2 import *
#from linearregressionpredictor3 import *
#from dnnpredictor import *
from nopredictor import *

from agglplanner2_utils import *


# C O N F I G U R A T I O N
number_of_threads = 0 #4
maxWorldIncrement = 4
maxCost = 2000000000000
stopWithFirstPlan = False
verbose = 1
maxTimeWaitAchieved = 0.0001
maxTimeWaitLimit = 200.



def sumActionCosts(node, last):
    ret = 0
    for t in node.costData[0:last]:
        ret += t[0]
    return ret

def computePlanCost(node):
    ret = 0
    iters = 0
    for xcost, xsuccess, xname in node.costData:
        iters += 1
        ret += xcost + (1-xsuccess)*sumActionCosts(node, iters)
    return ret



def setNewConstantsAsVariables(originalGraph, secondGraph):
    # Create a copy of the secondGraph
    outputGraph = copy.deepcopy(secondGraph)
    # Generate a list of node names
    existingNodes = [nodename for nodename in originalGraph.nodes]
    #
    outputGraph.nodes.clear()
    for nodename in secondGraph.nodes:
        if not nodename in existingNodes:
            nname = 'makeitavariable'+nodename
            outputGraph[nname] = secondGraph.nodes[nodename]
            outputGraph[nname].name = nname
    return outputGraph

## @brief Method heapsort. This method receives an iterable thing. It stores the iterable thing
# in a list and sorts the list.
# @param iterable is any iterable thing (like a list, a map...)
def heapsort(iterable):
    h = []
    for value in iterable:
        heapq.heappush(h, value)
    return [heapq.heappop(h) for i in range(len(h))]

##@brief This class stored the status and a lock.
class EndCondition(object):
    ##@brief Constructor Method. This method saves the status and the lock of the class.
    # @param status it is an optional parameter and, by default, his value is None.
    def __init__(self, status=None):
        ## Status of the class --> the status of the final condition
        self.status = status
        ## The lock for read and write the status
        self.lock = thread.allocate_lock()

    ##@brief Get Method. This method returns the status of the class. To do this, the method needs
    # to lock the other threads. This method reads a critical variable.
    # @retval ret is the status of the class.
    def get(self):
        self.lock.acquire()
        ret = self.status
        self.lock.release()
        return ret

    ##@brief Set method. This method changes the value of the status attribute. To do this, the
    # method needs to write in a critical memory zone, so it is necesary to lock it.
    # @param value is the new status
    def set(self, value):
        self.lock.acquire()
        self.status = value
        self.lock.release()



##@brief This method prints on the screen all the information of the new graph: the cost,
# the score, the number of actions and the names of the actions.
def printResult(result):
    print ('-----  R  E  S  U  L  T  S  -----')
    if verbose > 0:
        print ('Cost', result.cost)
        print ('Score', result.score)
        l = 0
        for action in result.history:
            if not (action[0] == '#' and action[1] != '!'):
                l += 1
        print ('Length', l)
        print ('Actions\n----------------')
    for action in result.history:
        #if action[0] != '#':
        print (action)

##@brief This is a class that implements a lockable list.
class LockableList():
    ##@brief Constructor Method. It initializes the list and the mutex.
    def __init__(self):
        ## The lockable list.
        self.thelist = []
        ## The mutex associated to the list.
        self.mutex = threading.RLock()

    ##@brief This method return the length of the lockable list.
    # @retval an integer that is the length of the list.
    def __len__(self):
        return len(self.thelist)

    ##@brief This method returns the item with the index or keyword a in the list.
    # @param a is the index or the keyword  of the item.
    # @retval the item that corresponds to the index a.
    def __getitem__(self, a):
        return self.thelist.__getitem__(a)

    ##@brief This method changes the item for the item b. Is necessary to lock the
    # the method, it changes a critical memory zone.-
    # @param a first item
    # @param b second item.
    def __setitem__(self, a, b):
        self.mutex.acquire()
        self.thelist.__setitem__(a, b)
        self.mutex.release()

    ##@brief This method return the iterator of the list.
    # @retval the iterator of the lockable list.
    def __iter__(self):
        return self.thelist.__iter__()

    ##@brief This method returns the size (the length) of the list.
    # This method needs acces to a critical memory zone, so it is necessary to
    # lock all the process.
    # @retval ret is an integer that is the size of the list.
    def size(self):
        self.mutex.acquire()
        ret = len(self.thelist)
        self.mutex.release()
        return ret

    ##@brief This method makes a pop on the list. First, it acquires the mutex in order to lock all the process.
    # Then It does a pop of the list (using the heappop class). And finally it releases the mutex.
    # @retval the pop of the list.
    def heapqPop(self):
        self.mutex.acquire()
        try:
            ret = heapq.heappop(self.thelist)
        finally:
            self.mutex.release()
        return ret

    ##@brief This method insert a value at the top of the list. It needs to acquire the mutex in order to lock all the process.
    # @param value the element to insert.
    def heapqPush(self, value):
        self.mutex.acquire()
        heapq.heappush(self.thelist, value)
        self.mutex.release()

    ##@brief The method returns the first element of the list. It needs to acquire the mutex in order to lock all the process. It doesnt remove the element of the list.
    # @retval the first element of the list
    def getFirstElement(self):
        self.mutex.acquire()
        ret = self.thelist[0]
        self.mutex.release()
        return ret

    ##@brief This method introduces an element at the end of the list. It needs to acquire the mutex in order to lock all the process.
    # @param v is the new element.
    def append(self, v):
        self.mutex.acquire()
        self.thelist.append(v)
        self.mutex.release()

    ##@brief This method pops an element from the list. It needs to acquire the mutex in order to lock all the process.
    # @param v is the new element.
    def pop(self):
        self.mutex.acquire()
        ret = self.thelist.pop()
        self.mutex.release()
        return ret

    ##@brief This method lock the mutex (it acquires him)
    def lock(self):
        self.mutex.acquire()

    ##@brief This method unlock the mutex (it releases him)
    def unlock(self):
        self.mutex.release()

    ##@brief This returns a copy
    def getList(self):
        self.mutex.acquire()
        r = copy.deepcopy(self.thelist)
        self.mutex.release()
        return r
    def __delitem__(self, index):
        self.mutex.acquire()
        del self.thelist[index]
        self.mutex.release()

##@brief This class defines an integer that can be locked and unlocked.
class LockableInteger(object):
    ##@brief constructor method. This method initializes the value of the integer and the
    # mutex of the class.
    # @param val is the initial value of the integer (it is an optional parameter).
    def __init__(self, val=0):
        ## The value of the integer
        self.value = val
        ## The mutex associated to the integer.
        self.mutex = threading.RLock()

    ##@brief This method changes the value of the integer. To do this, it needs to
    # take the mutex in order to lock all the process.
    # @param val the new value of the integer.
    def set(self, val):
        self.mutex.acquire()
        self.value = val
        self.mutex.release()

    ##@brief This method returns the value of the integer. It needs the mutex.
    # @retval ret is the value of the integer.
    def get(self):
        self.mutex.acquire()
        ret = self.value
        self.mutex.release()
        return ret

    ##@brief This method acquires the mutex (it locks him)
    def lock(self):
        self.mutex.acquire()

    ##@brief This method releases the mutex (it unlocks him).
    def unlock(self):
        self.mutex.release()

    ##@brief This method increases the value of the integer by one.
    # Like always, it needs to take the mutex.
    def increase(self):
        self.mutex.acquire()
        self.value += 1
        self.mutex.release()







class DomainInformation(object):
    def __init__(self, identifier, text):
        self.identifier = identifier
        self.text = text
        self.parsed = AGMFileDataParsing.fromText(text)
        self.plannerCode = self.parsed.getAGGLPlannerCode(skipPassiveRules=True)
        try:
            self.module = self.getModuleFromText(self.plannerCode).RuleSet()
        except:
            f = open('getModuleFromText_error.py', 'w')
            f.write(self.plannerCode)
            traceback.print_exc()
            print ('Code written to getModuleFromText_error.py')
            sys.exit(1)

    def getModuleFromText(self, moduleText):
        if len(moduleText) < 10:
            print ('len(moduleText) < 10')
            os._exit(-1)
        m = imp.new_module('domainModule'+str(self.identifier))
        try:
            exec (moduleText) in m.__dict__
        except:
            open("dede", 'w').write(moduleText)
            traceback.print_exc()
            sys.exit(1)
        return m


class TargetInformation(object):
    def __init__(self, identifier, text, domain):
        self.identifier = identifier
        self.domain = domain
        self.text = text
        self.code = generateTarget_AGGT(self.domain, AGMFileDataParsing.targetFromText(text))
        self.module    = self.getModuleFromText(self.code).CheckTarget
        self.variables = self.getModuleFromText(self.code).getTargetVariables
    def getModuleFromText(self, moduleText):
        if len(moduleText) < 10:
            print ('len(moduleText) < 10')
            os._exit(-1)
        m = imp.new_module('targetModule'+str(self.identifier))
        exec (moduleText) in m.__dict__
        return m


## @brief This is the main class. This makes all the process in order to create, check and execute the plan.
class AGGLPlanner2(object):
    ## @brief The constructor method. This initializes all the attributes of the class and makes the first check of the plan.
    # @param domainAGM  is the file name where is saved the grammar rules.
    # @param domainPath is the file name where is saved the grammar rules.
    # @param init is the XML file where is saved the inital status of the world
    # @param targetPath is the python file where is daved the target status of the world.
    # @param indent The intentation for the output plan
    # @param symbol_mapping mapping that should be used while planning (mainly used internally in recursive rules)
    # @param excludeList grammar rule black list  (those which can't be used for planning)
    # @param resultFile is the optional name of the file where the plan result will be stored.
    # @param decomposing: added whe we are decomposing a jerarchical rule
    # @param awakenRules: the set of rules that are currently available for the planner to find a solution
    def __init__(self, domainParsed, domainModule, initWorld, targetTuple, trainFile, indent=None, symbol_mapping=None, excludeList=None, resultFile=None, decomposing=False, awakenRules=set()):
        object.__init__(self)
        self.trainFile = trainFile
        self.timeElapsed = 0.
        self.symbol_mapping = copy.deepcopy(symbol_mapping)
        if excludeList == None: excludeList = []
        self.excludeList = copy.deepcopy(excludeList)
        self.indent = copy.deepcopy(indent)
        self.resultFile = resultFile
        target = targetTuple[0]
        self.targetFile = targetTuple[2]
        self.targetVariables_types, self.targetVariables_binary, self.targetVariables_unary = targetTuple[1]()
        if self.indent == None: self.indent = ''
        # Get initial world mdoel
        if isinstance(initWorld,unicode) or isinstance(initWorld,str):
            if '<AGMModel>' in initWorld:
                self.initWorld = WorldStateHistory([xmlModelParser.graphFromXMLText(initWorld), domainParsed.getInitiallyAwakeRules()|awakenRules])
            else:
                self.initWorld = WorldStateHistory([xmlModelParser.graphFromXMLFile(initWorld), domainParsed.getInitiallyAwakeRules()|awakenRules])
        elif isinstance(initWorld,AGMGraph):
            self.initWorld = WorldStateHistory([                                initWorld,  domainParsed.getInitiallyAwakeRules()|awakenRules])
        elif isinstance(initWorld,WorldStateHistory):
            self.initWorld = copy.deepcopy(initWorld)
        else:
            print (type (initWorld))
            os._exit(1)
        self.initWorld.nodeId = 0
        # Set rule and trigger maps
        self.domainParsed = domainParsed
        self.domainModule = domainModule
        self.awakenRules = awakenRules
        self.ruleMap = copy.deepcopy(domainModule.getRules()) #get all the active rules of the grammar
        self.triggerMap = copy.deepcopy(domainModule.getTriggers()) #get all the active rules of the grammar
        for e in excludeList:
            try:
                del self.ruleMap[e]  # delete the rules in excludeList from ruleMap
            except:
                pass
            try:
                del self.triggerMap[e]  # delete the rules in excludeList from triggerMap
            except:
                pass
        # Set target
        self.targetCode = target
        # Decomposing
        self.decomposing = decomposing
        # set stop flag
        self.externalStopFlag = LockableInteger(0)


    def setStopFlag(self):
        print ('got setStopFlag (internal class)')
        self.externalStopFlag.set(1)


    def getProbabilityDensityFunctionGenerator(self, trainFile):
        splitted = trainFile.split(':')
        if len(splitted)>2:
            print ('internal error f', trainFile)
            sys.exit(-1)
        method = splitted[0].lower()
        if method == 'naivebayes':
            return Generate(splitted[1])
        elif method == 'none':
            return NoPredictor(self.domainParsed)
        elif method == 'dummysemantics':
            return DummySemanticsPredictor(self.domainParsed)
        elif method == 'linearregression':
            return LinearRegressionPredictor(splitted[1])
        elif method == 'linearregression2':
            return LinearRegressionPredictor2(splitted[1])
        elif method == 'linearregression3':
            return LinearRegressionPredictor3(splitted[1])
        elif method == 'dnn':
            return DNNPredictor(splitted[1])
        else:
            print ('method', method, 'not supported')
            sys.exit(-1)

    def run(self):
        # Search initialization
        ## This attribute indicates the maximum size that can reach the graph
        self.maxWorldSize = maxWorldIncrement+len(self.initWorld.graph.nodes.keys())
        ## This attribute indicates the minimun cost of the open nodes of the graph
        self.minCostOnOpenNodes = LockableInteger(0)
        ## self.openNodes is a lockable list that contains all the open nodes of the state space that have not been completely explored.
        self.openNodes = LockableList()
        ## This is the lockable list of all the stales nodes
        self.staleNodes = LockableList()
        ## self.knownNodes is a lockable list that contains of all the know nodes of the graph, that is, those that have been completely explored.
        self.knownNodes = LockableList()
        ## This is the lockable list of all the calculated results.
        self.results = LockableList()
        ## This is the lockable integer of all the explored nodes
        self.explored = LockableInteger(0)
        ## This is the LockableInteger that stores the better cost of the solution
        self.cheapestSolutionCost = LockableInteger(-1)
        ## This is the condition to stop.
        self.end_condition = EndCondition()
        # We save in the list of the open nodes, the initial status of the world
        self.openNodes.heapqPush((0, copy.deepcopy(self.initWorld)))
        if verbose>1 and indent=='': print ('INIT'.ljust(20), self.initWorld)

        # Create initial state
        if self.symbol_mapping:
            self.initWorld.score, achieved, variables_achieved = self.targetCode(self.initWorld.graph, self.symbol_mapping)
        else:
            self.initWorld.score, achieved, variables_achieved = self.targetCode(self.initWorld.graph)

        types_achieved  = variables_achieved[0] & self.targetVariables_types
        binary_achieved = variables_achieved[1] & self.targetVariables_binary
        unary_achieved  = variables_achieved[2] & self.targetVariables_unary

        # Getting Action Preference data
        self.g = self.getProbabilityDensityFunctionGenerator(self.trainFile)
        self.g.domainParsed = self.domainParsed
        # Sorting actions by relevance   # #   Size of operator chunk   # #   TimeSlots for chunks
        self.threshData, chunkSize, chunkTime = self.g.get_distrb(types_achieved, binary_achieved, unary_achieved, self.initWorld.graph, self.targetVariables_types, self.targetVariables_binary, self.targetVariables_unary, self.targetFile)
        self.chunkSize = chunkSize
        self.chunkTime = chunkTime
        # print 'ACTIONS', sorted([ [x, self.threshData[x] ] for x in self.threshData ], reverse=True, key=itemgetter(1))
        # print self.threshData
        self.threshData = sorted(self.threshData, reverse=True, key=self.threshData.__getitem__)
        # print 'THRESHD2', self.threshData

        if achieved:
            # If the goal is achieved, we save the solution in the result list, the
            # solution cost in the cheapest solution cost and we put the end_condition
            # as goal achieved in order to stop the execution.
            self.results.append(self.initWorld)
            self.cheapestSolutionCost.set(self.results.getFirstElement().cost)
            if self.indent == '':
                 self.end_condition.set("GoalAchieved")
        elif number_of_threads>0:
            print ("Using multiple threads is not currently supported")
            # But, if the goal is not achieved and there are more than 0 thread running (1, 2...)
            # we creates a list where we will save the status of all the threads, take all
            # the threads (with their locks) and save it in the thread_locks list.
            # Run working threads
            ## This attributes is a list where we save all the thread that are running.
            self.thread_locks = []
            threadStatus = LockableList()
            for i in xrange(number_of_threads):
                lock = thread.allocate_lock()
                lock.acquire()
                threadStatus.append(True)
                self.thread_locks.append(lock)
                #                        def startThreadedWork( ruleMap,                 triggerMap,                     lock=None, i=0, threadPoolStatus=None):
                thread.start_new_thread(self.startThreadedWork, (copy.deepcopy(ruleMap), copy.deepcopy(self.triggerMap), lock, i, threadStatus))
            # Wait for the threads to stop
            for lock in self.thread_locks:
                lock.acquire()
        else:
            # If the solution is not achieved and there arent any thread to execute the programm
            # we stop it and show an error message.
            self.startThreadedWork(self.ruleMap, self.triggerMap)

        # We make others checks over the end_condition:
        #    -- If the end condition is wrong.
        #    -- or the end condition exceeded the maximum cost
        #    -- or we have found the best overcome.
        #    -- or we have achieved the goal
        #    -- or we have exceeded the maximum time limit
        #    -- or the end condition doesnt have any message
        # we print the correspond message
        if self.end_condition.get() == "IndexError":
            if verbose > 0: print ('End: state space exhausted (known', len(self.knownNodes), ' (open', len(self.openNodes))
        elif self.end_condition.get() == "MaxCostReached":
            if verbose > 0: print ('End: max cost reached')
        elif self.end_condition.get() == "BestSolutionFound":
            if verbose > 0: print ('End: best solution found')
        elif self.end_condition.get() == "GoalAchieved":
            if self.indent == '' and verbose > 0: print ('End: goal achieved')
        elif self.end_condition.get() == "TimeLimit":
            if verbose > 0: print ('End: TimeLimit')
        elif self.end_condition.get() == 'ExternalFlag':
            if verbose > 0: print ('End: External stop flag set')
            return AGGLPlannerPlan("__stopped__@{}\n", planFromText=True)
        elif self.end_condition.get() == None:
            if verbose > 0: print ('NDD:DD:D:EWJRI', self.end_condition, self)
        else:
            print ('UNKNOWN ERROR')
            print (self.end_condition.get())

##
##
##
        if len(self.results)>0: # If there are plans, proceed
            min_idx = 0
            for i in range(len(self.results)): # We go over all the actions of the plan, and we look for the best solution (the minimun cost).
                if self.results[i].cost < self.results[min_idx].cost:
                    min_idx = i
            i = min_idx

            if self.indent=='' and verbose > 0: print ('Got', len(self.results), 'plans!')

            try:
                plann = AGGLPlannerPlan([xx.split('@') for xx in self.results[i].history])
                n = copy.deepcopy(plann)
                while len(self.results[i].history)>0:
                    n = n.removeFirstAction(self.initWorld.graph)
                    #n = n.removeFirstActionDirect()
                    try:
                        check = agglplanchecker.AGGLPlanChecker(self.domainParsed, self.domainModule, self.initWorld, n, self.targetCode, self.symbol_mapping, verbose=False)
                        check.run()
                    except:
                        print ('Excepction!!')
                        traceback.print_exc()
                        break
                    if check.achieved:
                        print  ('  (removed)', self.results[i].history[0])
                        self.results[i].history = self.results[i].history[1:]
                        plann = copy.deepcopy(n)
                    else:
                        print  ('  (not removed)', self.results[i].history[0])
                        break
                if self.decomposing==False:
                    print ('ORIGINAL PLAN: ', self.results[i].cost)
                    for action in self.results[i].history:
                        print ('    ', action)
            except:
                traceback.print_exc()
                pass
            firstActionIsHierarchical = False
            if len(self.results[i].history) > 0:
                action = self.results[i].history[0]
                ac = AGGLPlannerAction(action)
                hierarchicalText = ''
                if ac.hierarchical:
                    self.excludeList.append(ac.name)
                    paramsWithoutNew = copy.deepcopy(ac.parameters)
                    for param in ac.parameters:
                        found = False
                        for arule in self.domainParsed.agm.rules:
                            if arule.name == ac.name:
                                if param in arule.lhs.nodes:
                                    found = True
                                    break
                        if not found:
                            #print 'removing fixed goal symbol', param
                            del paramsWithoutNew[param]
                            #paramsWithoutNew[param] = str('v')+str(paramsWithoutNew[param])
                    #print paramsWithoutNew
                    print ('\nDecomposing hierarchical rule ', ac.name, paramsWithoutNew)
                    """ We create an temporary state, without all the nodes created by the hierarchical rule"""
                    estadoIntermedio = self.triggerMap[ac.name](self.initWorld, ac.parameters)
                    """ We remove the constants created by the hierarchical rule, making them variables."""
                    graph = setNewConstantsAsVariables(self.initWorld.graph, estadoIntermedio.graph)
                    outputText = generateTarget_AGGT(self.domainParsed, {'graph':estadoIntermedio.graph, 'precondition': self.domainParsed.agm.getRule(ac.name).precondition})#, xgraph=estadoIntermedio.graph)
                    """ The following flag is set so the planning of the hierarchical rule is shown on screen"""
                    firstActionIsHierarchical = True
                    hierarchicalTarget = self.domainModule.getHierarchicalTargets()[ac.name]
                    hierarchicalTargetVariables = getattr(self.domainModule, ac.name+'_variables')
                    aaa = AGGLPlanner2( #domainParsed, domainModule, initWorld, targetTuple, threshData, indent=None, symbol_mapping=None, excludeList=None, resultFile=None, decomposing=False, awakenRules=set()):
                       self.domainParsed,
                       self.domainModule,
                       self.initWorld,
                       (hierarchicalTarget, hierarchicalTargetVariables, self.targetFile),
                       self.trainFile,
                       self.indent+'\t',
                       paramsWithoutNew,
                       self.excludeList,
                       self.resultFile,
                       True,
                       copy.deepcopy(self.results[i].awakenRules|self.awakenRules)
                    )
                    aaa.run()

                    self.results[i].history = self.results[i].history[1:] # The following two lines append a '#!' string to the first action (which is the hierarchical action thas has been decomposed)
                    self.results[i].history.insert(0, '#!'+str(ac))
                    print (self.results[i].history)
                    if len(aaa.results.getList()) == 0:
                        del self.results[:]
                    else:
                        h_min_idx = 0
                        h_retText = ''
                        for h_i in range(len(aaa.results)): # We go over all the actions of the plan, and we look for the best solution (the minimun cost).
                            if aaa.results[h_i].cost < aaa.results[h_min_idx].cost:
                                h_min_idx = h_i
                        for action in aaa.results[h_min_idx].history:
                            h_retText += str(action)+'\n'

                else:
                    firstActionIsHierarchical = False

            # if self.decomposing == False and firstActionIsHierarchical == True: print 'len results:', len(self.results)
            if len(self.results)>0: # If there are plans, proceed
                #printResult(self.results[i]) #the best solution
                retText = ''
                for action in self.results[i].history:
                    retText += str(action)+'\n'
                try:
                    finalPlan = AGGLPlannerPlan(h_retText + retText, planFromText=True)
                except:
                    finalPlan = AGGLPlannerPlan(retText, planFromText=True)
                if self.decomposing == False:
                    print ('FINAL PLAN WITH: ', len(finalPlan), ' ACTIONS:')
                    for action in finalPlan:
                        print ('    ', action)
                        if self.resultFile != None:
                            self.resultFile.write(str(action)+'\n')

                return finalPlan
            if self.indent=='' and verbose > 0: print ("----------------\nExplored", self.explored.get(), "nodes")

        if len(self.results)==0: # If the length of the list is zero, it means that we have not found a plan.
            if verbose > 0: print ('No plan found.')
##
##
##




    ##@brief This method starts the execution of program threads
    # @param ruleMap all the active rules of the grammar
    # @param lock this is the mutex of each thread.
    # @param i is the index (id) of the thread
    # @param threadPoolStatus this is the status of the thread. The threads have three possible status:
    #    1) On hold because they are waiting for another thread finishes his execution.
    #    2) Active. They are expanding a node.
    #    3) All the threads are idle because all of them have finished his executions.
    def startThreadedWork(self, ruleMap, triggerMap, lock=None, i=0, threadPoolStatus=None):
        if lock == None: # If there isnt any lock, we create one and we give it to the thread.
            lock = thread.allocate_lock()
            lock.acquire()

        if threadPoolStatus != None: # If the thread status is different of none, we lock the code and put the status of the i thread.
            threadPoolStatus.lock()
            threadPoolStatus[i] = True # the thread is working
            threadPoolStatus.unlock()
        # We take the initial time.
        timeA = datetime.datetime.now()

        # Chunk pointer
        chunkNumber = -1
        # known Flag
        knownFlag = False

        self.timeElapsed = -1.


        #
        # MAIN SEARCH LOOP
        #
        while True:
            #
            # Check stop conditions and compute the time spent
            #
            if self.externalStopFlag.get() != 0:
                self.end_condition.set('ExternalFlag')
                break
            # Again, we take the time and we calculated the elapsed time
            timeB = datetime.datetime.now()
            self.timeElapsed = float((timeB-timeA).seconds) + float((timeB-timeA).microseconds)/1e6
            # We take the length of the result list.
            nResults = self.results.size()
            # Check if we should give up because it already took too much time
            if self.timeElapsed > maxTimeWaitLimit or (self.timeElapsed > maxTimeWaitAchieved and nResults > 0):
                if nResults>0:
                    self.end_condition.set("GoalAchieved")
                else:
                    self.end_condition.set("TimeLimit")
                lock.release()
                return
            chunkNumber = (chunkNumber + 1)%len(self.chunkSize)
            if chunkNumber == len(self.chunkSize) - 1:
                knownFlag = True
            else:
                knownFlag = False

            while len(self.staleNodes) > 0:
                self.openNodes.heapqPush(self.staleNodes.heapqPop())


            # Loop shall ran for one chunk time
            selectedActions = self.threshData[0:int(len(self.threshData) * self.chunkSize[chunkNumber])]
            # if type(self.g) == LinearRegressionPredictor or type(self.g) == DNNPredictor:
             #     print 'SELECTED', selectedActions
            # print 'selectedActions', selectedActions
            while True:
                timeC = datetime.datetime.now()
                self.timeElapsed = float((timeC-timeA).seconds) + float((timeC-timeA).microseconds)/1e6
                timeElapsedChunk = float((timeC-timeB).seconds) + float((timeC-timeB).microseconds)/1e6
                nResults = self.results.size()
                if self.timeElapsed > maxTimeWaitLimit or (self.timeElapsed > maxTimeWaitAchieved and nResults > 0):
                    break
                if timeElapsedChunk >= self.chunkTime[chunkNumber]:
                    # print 'timeElapsedChunk >= self.chunkTime[chunkNumber]'
                    break
                if self.externalStopFlag.get() != 0:
                    self.end_condition.set('ExternalFlag')
                    break
                #
                # Pop an unexplored node from the queue, according to the heuristic. The popped node is stored in a variable named "head"
                #
                try:
                    # We take the head of the openNodes list: the first open node.
                    headNode = self.openNodes.heapqPop() # P O P   POP   p o p   pop
                    head = headNode[1]
                    if threadPoolStatus:
                        threadPoolStatus.lock()
                        threadPoolStatus[i] = True # We say that the thread i is active.
                        threadPoolStatus.unlock()
                    if knownFlag:
                        self.knownNodes.append(head)
                    else:
                        self.staleNodes.append(headNode)
                except:
                    # traceback.print_exc()
                    if not threadPoolStatus:
                        if chunkNumber!=len(self.chunkSize)-1: # we dont raise IndexError unless we are in the last chunk
                                print ('skipping chunk because the space state was exhausted for the current one')
                                break
                        self.end_condition.set("IndexError")
                        lock.release()
                        return
                    time.sleep(0.001)
                    threadPoolStatus.lock()
                    threadPoolStatus[i] = False
                    if not True in threadPoolStatus:
                        if chunkNumber!=len(self.chunkSize)-1: # we dont raise IndexError unless we are in the last chunk
                            print ('skipping chunk because the space state was exhausted for the current one')
                            break
                        self.end_condition.set("IndexError")
                        lock.release()
                        return
                    threadPoolStatus.unlock()
                    continue
                #
                # We now check other end conditions
                #
                # Update 'minCostOnOpenNodes', so we can stop when the minimum cost in the queue is bigger than one in the results
                self.updateMinCostOnOpenNodes(head.cost)
                # Check if we got to the maximum cost or the minimum solution
                if head.cost > maxCost:
                    self.end_condition.set("MaxCostReached")
                    lock.release()
                    return
                elif self.results.size()>0 and head.cost>self.cheapestSolutionCost.value and stopWithFirstPlan:
                    self.end_condition.set("GoalAchieved")
                    lock.release()
                    return
                #
                # For each action in the domain (for k in ruleMap) we generate the possible nodes of the state space that can
                # be reached from the state described in 'head'.
                #
                if verbose>5: print ('Expanding'.ljust(5), head)
                ######
                ###### HIGHLY EXPERIMENTAL CODE THAT COULD SAFELY BE REMOVED   S T A R T S
                ######
                if self.symbol_mapping:
                    kkscore, kkachieved, kkvariables_achieved = self.targetCode(head.graph, self.symbol_mapping)
                else:
                    kkscore, kkachieved, kkvariables_achieved = self.targetCode(head.graph)
                kktypes_achieved  = kkvariables_achieved[0] & self.targetVariables_types
                kkbinary_achieved = kkvariables_achieved[1] & self.targetVariables_binary
                kkunary_achieved  = kkvariables_achieved[2] & self.targetVariables_unary
                kkthreshData, kkchunkSize, kkchunkTime = self.g.get_distrb(kktypes_achieved, kkbinary_achieved, kkunary_achieved, head.graph, self.targetVariables_types, self.targetVariables_binary, self.targetVariables_unary, self.targetFile)
                kkthreshData = sorted(kkthreshData, reverse=True, key=kkthreshData.__getitem__)
                # print thres
                selectedActions = kkthreshData[0:int(len(kkthreshData) * kkchunkSize[chunkNumber])]
                # selectedActions = [ selectedActions[0] ]
                # print 'SEL('+str(kkchunkSize[chunkNumber])+'):', selectedActions
                ######
                ###### HIGHLY EXPERIMENTAL CODE THAT COULD SAFELY BE REMOVED   E N D S
                ######
                for k in selectedActions:
                    if k not in head.actionList and k in ruleMap:
                        head.actionList.append(k)
                        # Iterate over rules and generate derivates
                        if True:# k in head.awakenRules:
                            for deriv in ruleMap[k](head):
                                self.explored.increase()
                                if self.symbol_mapping:
                                    deriv.score, achieved, variables_achieved = self.targetCode(deriv.graph, self.symbol_mapping)
                                else:
                                    deriv.score, achieved, variables_achieved = self.targetCode(deriv.graph)
                                if achieved:
                                    self.results.append(deriv)
                                    if stopWithFirstPlan:
                                        self.end_condition.set("GoalAchieved")
                                        lock.release()
                                        return
                                    # Compute cheapest solution
                                    self.updateCheapestSolutionCostAndCutOpenNodes(self.results[0].cost)
                                self.knownNodes.lock()
                                notDerivInKnownNodes = not self.computeDerivInKnownNodes(deriv)
                                self.knownNodes.unlock()
                                self.staleNodes.lock()
                                notDerivInStaleNodes = not self.computeDerivInStaleNodes(deriv)
                                self.staleNodes.unlock()
                                if notDerivInKnownNodes and notDerivInStaleNodes:
                                    if deriv.stop == False:
                                        if len(deriv.graph.nodes.keys()) <= self.maxWorldSize:
                                            self.openNodes.heapqPush( (float(deriv.cost)-10.*float(deriv.score), deriv) ) # The more the better TAKES INTO ACCOUNT COST AND SCORE
                if verbose > 0:
                    doIt=False
                    nowNow = datetime.datetime.now()
                    try:
                        elap = (nowNow-self.lastTime).seconds + (nowNow-self.lastTime).microseconds/1e6
                        doIt = elap > 3
                    except:
                        self.lastTime = datetime.datetime.now()
                        doIt = True
                    if doIt:
                        self.lastTime = nowNow
                        print (str(int(self.timeElapsed)).zfill(10)+','+str(len(self.openNodes))+','+str(len(self.knownNodes))+','+str(head.score))


    def updateCheapestSolutionCostAndCutOpenNodes(self, cost):
        self.cheapestSolutionCost.lock()
        if cost >= self.cheapestSolutionCost.get():
            self.cheapestSolutionCost.unlock()
        else:
            self.openNodes.lock()
            self.cheapestSolutionCost.set(cost)

            newOpenNodes = LockableList()
            for node in self.openNodes:
                if node[1].cost < cost:
                    newOpenNodes.heapqPush(node)
            self.openNodes.thelist = newOpenNodes.thelist

            self.openNodes.unlock()
            self.cheapestSolutionCost.unlock()

    def updateMinCostOnOpenNodes(self, cost):
        self.minCostOnOpenNodes.lock()
        self.openNodes.lock()
        if cost < self.minCostOnOpenNodes.value:
            if self.getNumberOfOpenNodes()==0:
                self.minCostOnOpenNodes.value = 0
            else:
                self.minCostOnOpenNodes.value = self.firstOpenNode()[1].cost
                for n in self.openNodes:
                    if n[1].cost < self.minCostOnOpenNodes.value:
                        self.minCostOnOpenNodes.value = n[1].cost
        self.openNodes.unlock()
        self.minCostOnOpenNodes.unlock()

    def computeDerivInKnownNodes(self, deriv):
        for other in self.knownNodes:
            if deriv == other:
                if other.cost <= deriv.cost:
                    return True
        return False

    def  computeDerivInStaleNodes(self, deriv):
        for other in self.staleNodes:
            if deriv == other[1]:
                if other[1].cost <= deriv.cost:
                    return True
        return False



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
    #from pycallgraph import *
    #from pycallgraph.output import GraphvizOutput
    #graphviz = GraphvizOutput()
    #graphviz.output_file = 'basic.png'
    if True:
        #with PyCallGraph(output=graphviz):
        # We check if the program was run with all necessary arguments.
        # If there aren't all the arguments, we show an error mesage with how to use the program.
        # If there are all the arguments, we keep them in local variables.
        if len(sys.argv)<4:
            showHelp()
        domainFile = sys.argv[1] ## the file that contains the grammar rules
        initPath  = sys.argv[2] ## the file that contains the initial world status
        targetFile = sys.argv[3] ## the goal o target world status
        try:
            ## the file name where we keep the results of the program
            result = find_arg(sys.argv, '-o')
        except:
            showHelp()
        try:
            trainFile = find_arg(sys.argv, '-l') ## probability distribution generator
            if trainFile == None: trainFile = 'none'
        except:
            showHelp()
        trainList = trainFile.split(':')
        trainMethod = trainList[0].lower()
        print ('trainMethod', trainMethod)
        validMethods = [ 'none', 'naivebayes', 'dummysemantics', 'linearregression', 'linearregression2', 'linearregression3', 'dnn' ]
        if not trainMethod in validMethods:
            print ('ERROR:', trainMethod, 'not in the list of known learning methods: None, NaiveBayes, DummySemantics, LinearRegression, DNN\n')
            showHelp()
        trainList2 = [trainList[0].lower()]
        if len(trainList)>1:
            trainList2 += trainList[1:]
        trainFile = ':'.join(trainList2)
        print ('learning_algorithm:',trainFile)
        print ('\nGenerating search code...')
        ## Generate domain Python file
        # agmData is a variable of type AGMFileData, in AGGL.py file.
        # First: we CHECK the grammar. Is a parseAGGL.py's class
        # and we write the grammar in a python file.
        agmData = AGMFileDataParsing.fromFile(domainFile)
        agmData.generateAGGLPlannerCode("/tmp/domain.py", skipPassiveRules=True)

        ## Generate target Python file.
        if targetFile.lower().endswith('.aggt'):
            theTarget = AGMFileDataParsing.targetFromFile(targetFile)
            agglplanner2_utils.groundAutoTypesInTarget(theTarget, initPath)
            outputText = generateTarget_AGGT(agmData, theTarget)
        else:
            print (targetFile.lower())
            sys.exit(1)
        ## Save the python code of the target world status in the file target.py.
        ofile = open("/tmp/target.py", 'w')
        ofile.write(outputText)
        ofile.close()

        # Run planner
        # print 'RESULT', result
        # print 'TRAINN', trainFile
        domainAGM = AGMFileDataParsing.fromFile(sys.argv[1]) # From domain.aggl
        domainPath = "/tmp/domain.py"                        # ActiveRules.py path
        targetPath = "/tmp/target.py"                        # Target model or world.
        try:
            trainFile = sys.argv[5] # Sorting actions by relevance
        except:
            trainFile = 'none'

        if result:
            resultFile = open(result, 'w')
        else:
            resultFile = None

        hierarchicalInputPlan = None
        if len(sys.argv)>=8: hierarchicalInputPlan = open(sys.argv[7], 'r')

        domainRuleSet = imp.load_source('module__na_me', domainPath).RuleSet()
        targetCode = imp.load_source('modeeeule__na_me', targetPath).CheckTarget
        targetVariablesCode = imp.load_source('modeeeule__na_me', targetPath).getTargetVariables

        ## We store the initial or start time of the planner and call the agglplaner, the main program that makes all the process...
        start = time.time()
        #                domainParsed domainModule   initWorld                                                    targetTuple, trainfile  indent symbol_mapping excludeList, resultFile, decomposing, awakenRules)
        p = AGGLPlanner2(domainAGM,   domainRuleSet, initPath, (targetCode, targetVariablesCode, open(targetFile, 'r').read()), trainFile, '',    dict(),        [],         resultFile)
        p.run()
        end = time.time()
        print ('done\nRunning the planner...')
        print ('It took', end - start, 'seconds')
        if resultFile != None:
            resultFile.write("# time: " + str(end-start) + "\n")
