import sys, string
import json
sys.path.append('/usr/local/share/agm/')
from AGGL import *


def parsingJSON(file):
	print("Comienza el parseo del JSON")
	f = open(file)
	dsrmodel_dict = json.load(f)
	nodes = dict()
	listalinks=list()
	
	
	#print(dsrmodel_dict["DSRModel"]["symbols"])
	simbolos = dsrmodel_dict["DSRModel"]["symbols"]
	for symbol in simbolos:
		links_counter=0 # contador de enlaces válidos
		#COgemos las caracteristicas de cada elemento por su id
		elemento = simbolos[str(symbol)]
		id = elemento['id']
		x = elemento['attribute']['pos_x']['value']
		y = elemento['attribute']['pos_y']['value']
		type = elemento['type']
		#print(id,type, x, y)
		
		
		#Ahora necesitamos crear los enlaces
		links = elemento['links']
		for link in links:
			if link['label'] != 'RT':
				dst = link['dst']
				label = link['label']
				src = link['src']
				#print (dst, src, label)
				listalinks.append(AGMLink(src, dst, label, enabled=True))
				links_counter = links_counter + 1 # si el enlace encontrado no es RT, incrementa la variable
		
		# Si encuentra enlaces que no sean RTs, ese nodo se insertará para la navegación. Si el nodo no tiene enlaces a los que apunta o tiene enlaces RT, prácticamente es un nodo aislado y no se tendrá en cuenta para la navegación.
		if(links_counter!=0):
			nodes[id]= AGMSymbol(id, type, [x, y])
			
		
	grafo = AGMGraph(nodes, listalinks) 
	f.close()
	return grafo
	
#print(parsingJSON('mundodeprueba.json'))
