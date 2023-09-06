import osmnx as ox
import pickle
import numpy as np
import networkx as nx
from shapely.ops import linemerge
from multiprocessing import Pool
import random
import os
from os.path import exists
import tqdm
import matplotlib.pyplot as plt

#Steal kiwkqdrdist function from Bluesky
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

random.seed(0)
G = ox.load_graphml(filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_final.graphml")
nodes, edges = ox.graph_to_gdfs(G)


def generate_nodes(G):
    added_nodes = [] 
    coords = []

    while len(added_nodes) < 100:
        node = random.choice(list(G.nodes))
        node_lat = G.nodes[node]["y"]
        node_lon = G.nodes[node]["x"]
        node_too_close = False
        
        for node_entry in added_nodes:
            added_node_lat = G.nodes[node_entry]["y"]
            added_node_lon = G.nodes[node_entry]["x"]
            _, dist = kwikqdrdist(node_lat, node_lon, added_node_lat, added_node_lon)
            
            if dist <300:
                node_too_close = True
                break

        if not node_too_close:
            added_nodes.append(node)
            coords.append([node_lon, node_lat])

    return added_nodes

def generate_route_pickle(origin, destination):
    _ , dist = kwikqdrdist(G.nodes[origin]["y"], G.nodes[origin]["x"], G.nodes[destination]["y"], G.nodes[destination]["x"])
    print(origin)
    print(destination)
    print(dist)
    if exists(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles/{origin}-{destination}.pkl'):
        return
        
    if dist > 1000:
        try:
            route = nx.shortest_path(G, origin, destination)
        except:
            print(f"no path found between {origin} and {destination}")
            return
        else:
            route = nx.shortest_path(G, origin, destination)

        
        try:
            geoms = [edges.loc[(u, v, 0), 'geometry'] for u, v in zip(route[:-1], route[1:])]
        except:
            try:
                geoms = [edges.loc[(u, v, 1), 'geometry'] for u, v in zip(route[:-1], route[1:])]
            except:
                try:
                    geoms = [edges.loc[(u, v, 2), 'geometry'] for u, v in zip(route[:-1], route[1:])]
                except:
                    try:
                        geoms = [edges.loc[(u, v, 3), 'geometry'] for u, v in zip(route[:-1], route[1:])]
                    except:
                        geoms = [edges.loc[(u, v, 0), 'geometry'] for u, v in zip(route[:-1], route[1:])]
                    else:
                        geoms = [edges.loc[(u, v, 3), 'geometry'] for u, v in zip(route[:-1], route[1:])]
                    
                else:
                    geoms = [edges.loc[(u, v, 2), 'geometry'] for u, v in zip(route[:-1], route[1:])]
            else: 
                geoms = [edges.loc[(u, v, 1), 'geometry'] for u, v in zip(route[:-1], route[1:])]
        else: 
            geoms = [edges.loc[(u, v, 0), 'geometry'] for u, v in zip(route[:-1], route[1:])]
        line = linemerge(geoms)
        route_pickle = list(zip(line.xy[1],line.xy[0]))

    else: 
        return
    
    with open(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles/{origin}-{destination}.pkl' , 'wb') as f:
        pickle.dump(route_pickle, f)
    return route_pickle

def main():
    added_nodes = generate_nodes(G)
    print(added_nodes)
    for origin in added_nodes:
        for destination in added_nodes:
            if origin == destination:
                continue
            else:
                generate_route_pickle(origin, destination)
                
    #generate_route_pickle(42431508, 42454758)


if __name__ == "__main__":
    main()
    






            
#node_list = generate_nodes(G)







#node_df = nodes.loc[node_list]
#
#node_df.plot(   figsize=(15, 15),
#                cmap="viridis",
#                linewidth=.5,
#                scheme="headtailbreaks",
#                legend= True
#               ).set_axis_off()
#
#plt.show()


    



