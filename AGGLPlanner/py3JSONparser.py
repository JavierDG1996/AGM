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
#  Last Modification: Fernando Martín Ramos : 13/08/2021
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

# Python distribution imports
import sys, string
import json
sys.path.append('/usr/local/share/agm/')
from AGGL import *

#Entry:file-> JSON file that we are gonna parse.
#Exit: return a graph in a format that AGMPlanner can use to make the schedule
#Functionality: This function have the objetive of parse the JSON file that it receive on "file" parameter, returning a graph
#in a format that the program can use for make the plan.

def parsingJSON(file):
	print("Starting the JSON parsing")
	f = open(file)
	dsrmodel_dict = json.load(f)
	nodes = dict()
	listalinks=list()
	
	
	#print(dsrmodel_dict["DSRModel"]["symbols"])
	simbolos = dsrmodel_dict["DSRModel"]["symbols"]
	for symbol in simbolos:
		# We get the characteristics of each element based on its ide 
		elemento = simbolos[str(symbol)]
		id = elemento['id']
		x = elemento['attribute']['pos_x']['value']
		y = elemento['attribute']['pos_y']['value']
		type = elemento['type']
		#print(id,type, x, y)
		nodes[id]= AGMSymbol(id, type, [x, y])
		
		#We need to create the links
		links = elemento['links']
		for link in links:
			dst = link['dst']
			label = link['label']
			src = link['src']
			#print (dst, src, label)
			listalinks.append(AGMLink(src, dst, label, enabled=True))
			
		
	grafo = AGMGraph(nodes, listalinks) 
	f.close()
	return grafo
	
#print(parsingJSON('mundodeprueba.json'))
