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

#This file is designed to parse xml files in python 3, as the old parser was designed in python 2.


# Python distribution imports
import sys, string
import xml.etree.ElementTree as ET 
sys.path.append('/usr/local/share/agm/')
from AGGL import *


#Function parsingxml (file)
#Entry: file : the file we are gonna parse. Must be a .xml file.
#Exit: return the graph obatained after parse the xml file.
#Functionality: Parse the .xml file to a format that the AGMPlanner program can process.

def parsingxml(file):
        print('Comienzan mis pruebas')
        tree = ET.parse(file)
        nodes = dict()
        links=list()
        world = False
        currentSymbol = None
        print ('el tree es:',tree)
        root = tree.getroot()
        print ('el root es:',root)
        
        
        #Check the initial tag
        if root.tag.lower() != 'agmmodel':
            print ("<AGMModel> tag is missing!!")
            return 0
        #Si la etiqueta es correcta recorremos todo el arbol XML
        for child in root:
            #print (child.tag,child.attrib)
            
            #If it is a symbol
            if child.tag == 'symbol':
                print('es un simbolo')
                id = child.attrib['id']
                type = child.attrib['type']
                x = child.attrib['x']
                y = child.attrib['y']
                print('id=',id,' type=',type,' x=',x,' y=',y)
                nodes[id]= AGMSymbol(id, type, [x, y])
                
            #If it is a link   
            if child.tag == 'link':
                #print('es un enlace')
                src=child.attrib['src']
                dst=child.attrib['dst']
                label=child.attrib['label']
                #print('src=',src,' dst=',dst,' label=',label)
                
                # If the origin node or destiny node doesnt exist, there is an error.
                if not src in nodes:
                    print(('No src node', src))
                    sys.exit(-1)
                if not dst in nodes:
                    print(('No dst node', dst))
                    sys.exit(-1)
                    
                 #Check if the link is deactivated in the XML       
                enabled = True
                try:
                    if child.attrib['enabled'].lower() in ["false", "f", "fa", "fal", "fals", "0", "n", "no"]:
                        enabled = False
                except:
                    pass

                links.append(AGMLink(src, dst, label, enabled=enabled))
                
        grafo = AGMGraph(nodes, links)      
        print(grafo)  
        return grafo

