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


gdf_nodes = gpd.read_file(r"C:\Users\Jason\Documents\Thesis\nodes.gpkg", layer='nodes').set_index('osmid')
gdf_edges = gpd.read_file(r"C:\Users\Jason\Documents\Thesis\edges.gpkg", layer='edges').set_index(['u', 'v', 'key'])

gdf_nodes= gdf_nodes.drop(gdf_nodes.index[gdf_nodes["geometry"] == None].tolist())
gdf_edges= gdf_edges.drop(gdf_edges.index[gdf_edges["geometry"] == None].tolist())
gdf_nodes= gdf_nodes.drop(columns= ["highway", "street_count", "ref", "selected"])
gdf_edges= gdf_edges.drop(columns=["from", "to"])

#for i in range(len(gdf_nodes)):
#    gdf_nodes["geometry"].iloc[i]= ox.projection.project_geometry(gdf_nodes["geometry"].iloc[i], crs="EPSG:4087",to_crs = 'epsg:4326')
#print(gdf_nodes)
#for i in range(len(gdf_edges)):
#    gdf_edges["geometry"].iloc[i]= ox.projection.project_geometry(gdf_edges["geometry"].iloc[i], crs="EPSG:4087",to_crs = 'epsg:4326')
#print(gdf_edges)



gdf_nodes= gdf_nodes.to_crs(crs = 'epsg:4326')
gdf_edges= gdf_edges.to_crs(crs = 'epsg:4326')

gdf_nodes["x"] = gdf_nodes["geometry"].x
gdf_nodes["y"] = gdf_nodes["geometry"].y


print(gdf_nodes.index)

G = ox.graph_from_gdfs(gdf_nodes, gdf_edges)

#ox.plot_graph(G)
#plt.show()
#G= ox.projection.project_graph(G, to_crs = 'epsg:4326')
#nodes, edges= ox.graph_to_gdfs(G)
#print(edges["geometry"][edges["stroke_group"] == 979].iloc[0])


G = ox.distance.add_edge_lengths(G)



G_reversed = G.reverse()
#
#G_reversed = ox.distance.add_edge_lengths(G_reversed)


#ox.save_graphml(G, filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G.graphml")
#ox.save_graphml(G_reversed, filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_reversed.graphml")
#export = ox.save_graph_geopackage(G, filepath= r"C:\Users\Jason\Documents\Thesis\Network data\finalG3.gpkg")

#streets = ox.load_graphml(filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G.graphml")






