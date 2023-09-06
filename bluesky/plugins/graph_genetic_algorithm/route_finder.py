import bluesky as bs
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import shapely
import numpy as np
import random
import math
import momepy
from collections import Counter
from graph_builder import GraphBuilder
from evaluate_directionality import dijkstra_search
import pickle
from multiprocessing import Pool

G = ox.load_graphml(filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_final.graphml")
routes = pd.DataFrame(columns = ["Origin", "Destination" , "Route"])
osmnx_keys_list= list(G._node.keys())

count = 0

for i in range(len(osmnx_keys_list)):
    origin = osmnx_keys_list[i]
    for j in range(len(osmnx_keys_list)):
        destination = osmnx_keys_list[j]
        route = ox.shortest_path(G, origin, destination)
        if route == None:
            count += 1
            #print(" No path can be found between " + str(origin) + " and " + str(destination))
        
        else:
            routes.loc[len(routes)] = [origin , destination , route]


with open('routes.pkl', 'wb') as f:  # open a text file
    pickle.dump(routes, f) # serialize the list
    
f.close()

print(count)
print(routes)



