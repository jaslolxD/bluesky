#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 12 11:14:29 2021

@author: andreibadea
"""

# Based on:
# https://github.com/DEAP/deap/blob/master/examples/ga/onemax.py

# Derek M Tishler
# Jul 2020
import random

import numpy as np

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

import osmnx as ox
from evaluate_directionality import dijkstra_search_multiple
from graph_builder import GraphBuilder
import random
import copy

##Ray init code, user needs to apply#################
# see: https://docs.ray.io/en/master/walkthrough.html
import ray
from ray_map import ray_deap_map

class Node:
    def __init__(self,key,x,y):
        self.key=key
        self.x=x
        self.y=y
        self.children={}# each element of neigh is like [ox_key,edge_cost] 
        
gis_data_path = "c:\\Users\\Jason\\Documents\\Thesis\\Network data"
direction_0_name = 'G.graphml' #Default direction
direction_1_name = 'G_reversed.graphml' #Reversed direction
GB = GraphBuilder(gis_data_path, direction_0_name, direction_1_name)

# Destinations and origins here. We'll try to find the path from every point to every other point.
#coords = np.array([[-74.0083657 , 40.7166018],
#                   [-74.008269 , 40.7077219],
#                   [-74.006076 , 40.7099178],
#                   [-73.9939452 , 40.7137475],
#                   [-74.011576 , 40.7040261],
#                   [-73.9870806 , 40.7136336],
#                   [-73.9906322 , 40.7207678],
#                   [-73.9954604 , 40.7216242],
#                   [-73.9963251 , 40.7176001],
#                   [-73.991452 , 40.7174356],
#                   [-73.989429 , 40.726188],
#                   [-73.9792686 , 40.7234983],
#                   [-73.978998 , 40.728106],
#                   [-73.9876833 , 40.7326041],
#                   [-73.982267 , 40.73602],
#                   [-73.992792 , 40.733922],
#                   [-73.9527041 , 40.7765623],
#                   [-73.9574004 , 40.7701167],
#                   [-73.9793024 , 40.7767307],
#                   [-73.9665628 , 40.7891218],
#                   [-73.9773679 , 40.7895635],
#                   [-73.9628734 , 40.7992437],
#                   [-73.9544117 , 40.805728],
#                   [-73.9452763 , 40.8259476],
#                   [-73.932861 , 40.850506],
#                   [-73.935653 , 40.844201],
#                   [-73.9395229 , 40.847842],
#                   [-73.9243885 , 40.8653705]])

coords = np.array([[-73.9795963, 40.7496466], [-73.985242, 40.733372], [-73.9703363, 40.78905879999999], [-73.9904253, 40.76654799999999], [-73.9899392, 40.71121879999998], [-73.9436083, 40.7985684], [-74.0058581, 40.73313459999999], [-73.9471053, 40.825900999999995], [-73.9524444, 40.786509300000006], [-73.994153, 40.722722999999995], [-73.9170603, 40.8636939], [-74.0112905, 40.7251837], [-73.941078, 40.829083], [-73.9839423, 40.7754121], [-74.0137834, 40.7024066], [-73.9818317, 40.77958420000001], [-73.9897914, 40.7572335], [-73.9444103, 40.846757099999984], [-73.9441039, 40.83537150000001], [-73.93924690000001, 40.8418306], [-73.950941, 40.77071709999999], [-73.9374253, 40.80438019999999], [-73.9465427, 40.816506499999996], [-73.9408517, 40.8083381], [-73.9502721, 40.8064478], [-73.9909579, 40.724109200000015], [-73.9572984, 40.7802244], [-73.933312, 40.855335], [-73.98528180000001, 40.7236472], [-73.988561, 40.76911749999999], [-73.9704329, 40.74578259999999], [-73.9251086, 40.8614188], [-73.9429425, 40.7840873], [-73.9927007, 40.76342770000001], [-73.962392, 40.7999177], [-73.9768235, 40.743504699999995], [-74.0105666, 40.7138543], [-73.9852411, 40.73884629999999], [-73.9355668, 40.84170050000001], [-73.974319, 40.74578269999999], [-74.0084893, 40.7502524], [-73.9693692, 40.80368289999999], [-73.9944724, 40.755910400000005], [-73.9638565, 40.757020499999996], [-74.0020342, 40.73812960000001], [-74.006498, 40.736957000000004], [-73.9325826, 40.8642506], [-74.0079472, 40.7236541], [-73.953014, 40.82582], [-73.9529821, 40.79172179999999], [-73.9535288, 40.8136722], [-73.9282354, 40.8571635], [-73.9722665, 40.796561200000006], [-73.938504, 40.8222778], [-73.9886291, 40.737169899999984], [-73.9684561, 40.799067699999995], [-73.9927979, 40.7429103], [-73.9985565, 40.745341100000005], [-74.0171151, 40.70747169999999], [-73.98287270000002, 40.76671569999999], [-73.934686, 40.84551999999999], [-73.9988397, 40.7601736], [-73.9323176, 40.80454039999999], [-73.94664, 40.838058], [-73.990255, 40.77398979999999], [-73.961955, 40.759623100000006], [-73.9795551, 40.7381901], [-73.9914619, 40.7317445], [-73.9954452, 40.7160039], [-73.9457066, 40.777874000000004], [-73.92125, 40.86411199999999], [-73.9492747, 40.8027375], [-73.9817513, 40.74638869999999], [-73.9952571, 40.7198711], [-74.008199, 40.7421069], [-73.9437242, 40.7928745], [-74.0152427, 40.71601030000001], [-74.003236, 40.74897399999998], [-73.9721811, 40.7864968], [-73.995585, 40.7282036], [-73.95612360000001, 40.81885069999999], [-73.9677191, 40.762873600000006], [-73.999234, 40.71891299999999], [-73.945968, 40.801342], [-73.96775570000001, 40.76860039999999], [-73.9542439, 40.76618320000001], [-73.92032, 40.86900099999999], [-74.0147291, 40.7098267], [-73.95631, 40.82312760000001], [-73.9768477, 40.71461949999999], [-73.9996618, 40.7340688], [-73.978792, 40.7198786], [-73.9886624, 40.742832], [-73.9768851, 40.7958825], [-73.9460871, 40.7896375], [-73.9596517, 40.820329099999995], [-73.9578259, 40.8151611], [-74.005535, 40.745816], [-74.0024719, 40.75511929999998], [-73.9610036, 40.811789299999994]])

#np.array([[-74.01120790000002, 40.710369199999995],
         #          [-73.9870806, 40.713633599999994],
         #          [-74.002513, 40.727601],
         #          [-73.9831222, 40.734845799999995],
         #          [-73.9958428, 40.75407130000001],
         #          [-73.9638433 , 40.7653085],
         #          [-73.9726774, 40.7908816],
         #          [-73.9421243, 40.79794999999999],
         #          [-73.9540766, 40.8163558],
         #          [-73.937782 , 40.82849999999999],
         #          [-73.9357231, 40.85017639999998],
         #          [-73.920612, 40.86675900000001],
         #          
         #          [-73.9805314, 40.7648393],
         #          [-74.0104958, 40.7181153],
         #          [-73.9894017, 40.762861699999995],
         #          [-73.933731, 40.84932099999999],
         #          [-73.941503, 40.791908],
         #          [-74.008845, 40.727470000000004]])

# %%
nodes = ox.nearest_nodes(GB.G_0, coords[:,0], coords[:,1])

orig_nodes_numbers = copy.copy(nodes)

dest_nodes_numbers = copy.copy(nodes)


ray.shutdown()
ray.init(num_cpus=4)

'''
Eval is made arbitrarily more expensive to show difference. Tricky as DeltaPenalty skips evals sometimes.
'time python onemax_ray.py' on my machine(8 processors) shows:
num_cpus=1 (map): 25.5 sec(real)
num_cpus=2 (ray): 17.5 sec(real)
num_cpus=4 (ray): 13.0 sec(real)
num_cpus=7 (ray): 13.3 sec(real)
num_cpus=8 (ray): 13.6 sec(real)
'''
######################################################


##Example code updated, user needs to apply##########
def creator_setup():
    creator.create("FitnessMin", base.Fitness, weights = (-1.0,))
    creator.create("Individual", list , fitness = creator.FitnessMin)
# make sure to call locally
creator_setup()
######################################################

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_bool", random.randint, 0, 1)

# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, 
                 toolbox.attr_bool, len(GB.stroke_groups))
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

def evalOneMax(individual):
    # Make a copy
    dest_nodes = copy.copy(dest_nodes_numbers)
            
    # reoroder edge geodatframe
    G = GB.build_graph(individual)
    
    # Process nodes to put em in the right form
    omsnx_keys_list=list(G._node.keys())
    
    ###Initialise the graph for the search
    graph={}
    for i in range(len(omsnx_keys_list)):
        key=omsnx_keys_list[i]
        x=G._node[key]['x']
        y=G._node[key]['y']
        node=Node(key,x,y)
        children=list(G._succ[key].keys())
        for ch in children:
            try:
                cost=G[key][ch][0]['length']
            except:
                 try:
                     cost=G[key][ch][1]['length']
                 except:
                     cost=G[key][ch][2]['length']
                 else:
                     cost=G[key][ch][1]['length']
            else:
                 cost=G[key][ch][0]['length']

            node.children[ch]=cost
        
        graph[key]=node
    orig_nodes = []
    for i, node in enumerate(orig_nodes_numbers):
        orig_nodes.append(graph[node])
    
    # Get cost
    total_cost = dijkstra_search_multiple(graph, orig_nodes, dest_nodes)
    print('--------------------------------------')
    print(individual)
    print(f'Cost for this individual: {total_cost}')
    return total_cost


toolbox.register("evaluate", evalOneMax)
# Here we apply a feasible constraint: 
# https://deap.readthedocs.io/en/master/tutorials/advanced/constraints.html

toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
toolbox.register("select", tools.selTournament, tournsize=3)

##This is different!#################################
#toolbox.register("map", ray_deap_map, creator_setup = creator_setup)
######################################################

if __name__ == "__main__":
    pop = toolbox.population(n=6)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)

    algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=1000, 
                        stats=stats, halloffame=hof)
    # Shutdown at the end
    ray.shutdown()