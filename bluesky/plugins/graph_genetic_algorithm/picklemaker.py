import osmnx as ox
import pickle
import numpy as np
import geopandas as gpd
import networkx as nx
from shapely.ops import linemerge
from multiprocessing import Pool
import random
import tqdm
import os
from os.path import exists
import tqdm
import matplotlib.pyplot as plt
from multiprocessing import Pool

nm  = 1852. 

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
nodes = gpd.read_file("bluesky/plugins/graph_genetic_algorithm/gen_directed.gpkg", layer = 'nodes')
edges = gpd.read_file("bluesky/plugins/graph_genetic_algorithm/gen_directed.gpkg", layer = 'edges')
edges.set_index(['u', 'v', 'key'], inplace=True)
nodes.set_index(['osmid'], inplace=True)

# ensure that it has the correct value
nodes['x'] = nodes['geometry'].apply(lambda x: x.x)
nodes['y'] = nodes['geometry'].apply(lambda x: x.y)
G = ox.graph_from_gdfs(nodes, edges)


def generate_nodes(G):
    added_orig_nodes = [] 
    added_dest_nodes = []

    while len(added_orig_nodes) < 200:
        node = random.choice(list(G.nodes))
        node_lat = G.nodes[node]["y"]
        node_lon = G.nodes[node]["x"]
        node_too_close = False
        
        if node in added_orig_nodes:
            continue
        
        for node_entry in added_orig_nodes:
            added_node_lat = G.nodes[node_entry]["y"]
            added_node_lon = G.nodes[node_entry]["x"]
            _, dist = kwikqdrdist(node_lat, node_lon, added_node_lat, added_node_lon)
            dist = dist * nm
            
            if dist < 500:
                node_too_close = True
                break

        if not node_too_close:
            added_orig_nodes.append(node)
    
    while len(added_dest_nodes) < 200:
        node = random.choice(list(G.nodes))
        node_lat = G.nodes[node]["y"]
        node_lon = G.nodes[node]["x"]
        node_too_close = False
        
        if node in added_orig_nodes or node in added_dest_nodes:
            continue
        
        for node_entry in added_dest_nodes:
            added_node_lat = G.nodes[node_entry]["y"]
            added_node_lon = G.nodes[node_entry]["x"]
            _, dist = kwikqdrdist(node_lat, node_lon, added_node_lat, added_node_lon)
            dist = dist * nm
            
            if dist < 500:
                node_too_close = True
                break

        if not node_too_close:
            added_dest_nodes.append(node)

    return added_orig_nodes, added_dest_nodes

def generate_route_pickle(input):
    origin, destination = input
    _ , dist = kwikqdrdist(G.nodes[origin]["y"], G.nodes[origin]["x"], G.nodes[destination]["y"], G.nodes[destination]["x"])
    dist *= nm
        
    if dist > 5000:
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
    
    with open(f'bluesky/plugins/graph_genetic_algorithm/pickles/{origin}-{destination}.pkl' , 'wb') as f:
        pickle.dump(route_pickle, f)
    return route_pickle

def main():
    input_arr = []
    added_orig_nodes, added_dest_nodes = generate_nodes(G)
    for origin in added_orig_nodes:
        for destination in added_dest_nodes:
            input_arr.append((origin, destination))
            #generate_route_pickle(origin, destination)
            
    with Pool(4) as p:
        _ = list(tqdm.tqdm(p.imap(generate_route_pickle, input_arr), total = len(input_arr)))


if __name__ == "__main__":
    main()