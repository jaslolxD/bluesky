import bluesky as bs
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.ops import linemerge
import numpy as np
import random
import math
import momepy
from collections import Counter
from graph_builder import GraphBuilder
import pickle
import os

def kwikqdrdist(lata, lona, latb, lonb):
    """Gives quick and dirty qdr[deg] and dist [nm]
       from lat/lon. (note: does not work well close to poles)"""

    re      = 6371000.  # radius earth [m]
    dlat    = np.radians(latb - lata)
    dlon    = np.radians(((lonb - lona)+180)%360-180)
    cavelat = np.cos(np.radians(lata + latb) * 0.5)

    dangle  = np.sqrt(dlat * dlat + dlon * dlon * cavelat * cavelat)
    dist    = re * dangle

    qdr     = np.degrees(np.arctan2(dlon * cavelat, dlat)) % 360

    return qdr, dist

def load_gdf():
    gdf_nodes = gpd.read_file(r"C:\Users\Jason\Documents\Thesis\Network data\nodes.gpkg", layer='nodes').set_index('osmid')
    gdf_edges = gpd.read_file(r"C:\Users\Jason\Documents\Thesis\Network data\edges.gpkg", layer='edges').set_index(['u', 'v', 'key'])

    gdf_nodes= gdf_nodes.drop(gdf_nodes.index[gdf_nodes["geometry"] == None].tolist())
    gdf_edges= gdf_edges.drop(gdf_edges.index[gdf_edges["geometry"] == None].tolist())
    return gdf_nodes, gdf_edges

def load_graph():
    G = ox.load_graphml(filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G.graphml")
    G_reversed = ox.load_graphml(filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_reversed.graphml")
    return G, G_reversed

def removeUnused(gdf_nodes, gdf_edges):
    gdf_nodes= gdf_nodes.drop(gdf_nodes.index[gdf_nodes["geometry"] == None].tolist())
    gdf_edges= gdf_edges.drop(gdf_edges.index[gdf_edges["geometry"] == None].tolist())
    return(gdf_nodes, gdf_edges)

def singleLaneFilter(gdf_edges):
    lst_index = []
    unique_index = []
    check = False
    check = False
    counter = 0
    while check == False:
        for entry in gdf_edges.index:
            lst_index += list(entry[0:2])

        unique_index = [k for k, v in Counter(lst_index).items() if v == 1]
        for entry in unique_index:
            if len(gdf_edges.query("u== " + str(entry))) != 0:
                gdf_edges = gdf_edges.drop(index = entry, level = "u")

            else: 
                gdf_edges = gdf_edges.drop(index = entry, level = "v")

        if len(unique_index) ==0:
            print("passed")
            check = True

    return gdf_edges

def reArrangeStrokeNumber(gdf_edges):
    stroke_list = list(gdf_edges["stroke_group"])
    unique_strokes = list(set(stroke_list)) #for testing
    count = 0
    for i in range(gdf_edges.stroke_group.max()+1):
        if len(gdf_edges["stroke_group"][gdf_edges["stroke_group"] == i]) != 0:
            gdf_edges.loc[gdf_edges["stroke_group"] == i, "stroke_group"] = count
            count += 1
    return gdf_edges

def export_geopackage(gdf_nodes, gdf_edges):
    gdf_nodes.to_file(r'C:\Users\Jason\Documents\Thesis\Network data\nodes.gpkg', driver='GPKG', layer="nodes" ) 
    gdf_edges.to_file(r'C:\Users\Jason\Documents\Thesis\Network data\edges.gpkg', driver='GPKG', layer="edges" ) 

def export_graph(gdf_nodes, gdf_edges):
    G = ox.graph_from_gdfs(gdf_nodes, gdf_edges)
    G = ox.distance.add_edge_lengths(G)
    G_reversed = G.reverse()
    ox.save_graphml(G, filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G.graphml")
    ox.save_graphml(G_reversed, filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_reversed.graphml")

#G, G_reversed = load_graph()
#
#ox.save_graph_geopackage(G, filepath= r'C:\Users\Jason\Documents\Thesis\Network data\Graph_OG.gpkg')
#ox.save_graph_geopackage(G_reversed, filepath= r'C:\Users\Jason\Documents\Thesis\Network data\Graph_reversed.gpkg')

#gis_data_path = "c:\\Users\\Jason\\Documents\\Thesis\\Network data"
#direction_0_name = 'G.graphml' #Default direction
#direction_1_name = 'G_reversed.graphml' #Reversed direction
#GB = GraphBuilder(gis_data_path, direction_0_name, direction_1_name)
#Iteration12 = [1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1]
#G = GB.build_graph(Iteration12)
#G = ox.save_graphml(G, filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_final.graphml")


#_ , dist = kwikqdrdist(G.nodes[42431508]["y"], G.nodes[42431508]["x"], G.nodes[42454758]["y"], G.nodes[42454758]["x"])
#print(dist)
#route = nx.shortest_path(G, 42431508, 42454758)
#
##print(edges.loc[(42431508, 42454758,0), "geometry"])
#print(edges.loc[1061531695])

#geoms = [edges.loc[(u, v, 0), 'geometry'] for u, v in zip(route[:-1], route[1:])]
#line = linemerge(geoms)
#route_pickle = list(zip(line.xy[1],line.xy[0]))


#x = pd.read_pickle(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles/42431461-42442625.pkl')
#print(x)



lst = os.listdir(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles')
filename = lst[0]

x = pd.read_pickle(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles/{filename}')
print(x)
#for entry in x:
#    print(entry[0])
#    print(entry[1])