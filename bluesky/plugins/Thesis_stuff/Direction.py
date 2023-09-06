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

file = r"C:\Users\Jason\Documents\Thesis\graph.gpkg"

#edges= gpd.read_file(r"C:\Users\Jason\Documents\Thesis\edges.gpkg")
#nodes= gpd.read_file(r"C:\Users\Jason\Documents\Thesis\nodes.gpkg")

gdf_nodes = gpd.read_file(file, layer='nodes').set_index('osmid')
gdf_edges = gpd.read_file(file, layer='edges').set_index(['u', 'v', 'key'])


gdf_nodes["x"] = gdf_nodes["geometry"].x
gdf_nodes["y"] = gdf_nodes["geometry"].y
gdf_edges= gdf_edges.drop(gdf_edges.index[gdf_edges["geometry"] == None].tolist())
gdf_edges["direction"]= ""



for i in range(gdf_edges.stroke_group.max()):
    lst = []
    for linestring in gdf_edges["geometry"][gdf_edges["stroke_group"] == i].values:
        lst.append(linestring.coords[0])
        lst.append(linestring.coords[-1])
        
    lst = [k for k, v in Counter(lst).items() if v == 1]
        
    if len(lst) == 0:
        gdf_edges["direction"].loc[gdf_edges["stroke_group"] == i] = "NS"

    elif len(lst) == 2:
        bearing = math.degrees(math.atan2(lst[0][1] -lst[1][1], lst[0][0]- lst[1][0]))
        if 17<= bearing <= 107 or -163 <= bearing <= -73:
            gdf_edges["direction"].loc[gdf_edges["stroke_group"] == i] = "NS"

        else:
            gdf_edges["direction"].loc[gdf_edges["stroke_group"] == i] = "EW"

    else:
        print("Amount of elements is wrong for " + str(i))
        gdf_edges["direction"].loc[gdf_edges["stroke_group"] == i] = "EW"


print(gdf_edges["direction"])

assert gdf_nodes.index.is_unique and gdf_edges.index.is_unique
G = ox.graph_from_gdfs(gdf_nodes, gdf_edges)

#gdf_nodes.to_file(r'C:\Users\Jason\Documents\Thesis\nodes.gpkg', driver='GPKG', layer="nodes" ) 
#gdf_edges.to_file(r'C:\Users\Jason\Documents\Thesis\edges.gpkg', driver='GPKG', layer="edges" ) 


#print(gdf_edges["geometry"])

#fig,ax = ox.plot_graph(G)
#plt.show()

#print(edges.index)
#print(type(edges.values[0]))
#
#for i in range(len(edges.values)):
#    if type(edges.values[i]) != np.ndarray:
#        print(edges.values[i])
#        print(edges.iloc[i])
#print(edges.iloc[0])

#print(edges.columns)

#new_G= ox.graph_from_gdfs(nodes, edges)



#final_gdf= pd.concat([EW_gdf,NS_gdf])
#final_gdf= final_gdf.set_crs("EPSG:4087", allow_override= True)

#final_gdf.plot(final_gdf.directionality,
#               figsize=(15, 15),
#                cmap="viridis",
#                linewidth=.5,
#                scheme="headtailbreaks",
#                legend= True
#               ).set_axis_off()
#plt.show()