import bluesky as bs
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import shapely
import random
import math
import momepy

place_name = "Garment District, New York, USA"
#Manhattan = ox.graph_from_place(place_name, network_type='drive')
#ox.save_graphml(Manhattan, filepath= r"C:\Users\Jason\Documents\Thesis\graph.graphml")
Manhattan= ox.load_graphml(r"C:\Users\Jason\Documents\Thesis\graph.graphml")
Manhattan= ox.projection.project_graph(Manhattan)
nodes, edges= ox.graph_to_gdfs(ox.get_undirected(Manhattan))
edges= edges.drop(edges.index[edges["tunnel"] == edges["tunnel"]].tolist())
edges=edges.drop(columns=["name", "highway", "maxspeed", "oneway", "reversed", "length", "from","to","lanes", 'ref', 'access', 'junction',
       'bridge', 'tunnel', 'width'])
                               
continuity = momepy.COINS(edges)
edges["stroke_group"] = continuity.stroke_attribute()

print(edges.stroke_group.max())


#for i in range(992):
#    print(edges[edges["stroke_group"]== i])





G_new = ox.graph_from_gdfs(nodes, edges)
export = ox.save_graph_geopackage(G_new, filepath= r"C:\Users\Jason\Documents\Thesis\graph.gpkg")
fig,ax = ox.plot_graph(G_new)
plt.show()





#edges[edges.stroke_group == 908].plot(
#               figsize=(15, 15),
#                cmap="viridis",
#                linewidth=.5,
#                scheme="headtailbreaks",
#                legend= True
#               ).set_axis_off()
#plt.show()





#for j in range(len(stroke_gdf)):
#    if type(stroke_gdf.geometry[j]) == shapely.geometry.multilinestring.MultiLineString:
#        for line in stroke_gdf.geometry[j].geoms:
#            linestringlist=[line.coords[0]]
#            
#            i=1
#            while i != len(line.coords)-1:
#                a= line.coords[i-1]
#                b = line.coords[i]
#                c = line.coords[i+1]
#                angle1 = math.degrees(math.atan2(a[1] -b[1], a[0]-b[0]))
#                angle2= math.degrees(math.atan2(b[1] -c[1], b[0]-c[0]))
#
#
#                if abs(angle1-angle2) > 45:
#                     linestringlist.append(line.coords[i])
#                     geometry.append(shapely.LineString(linestringlist))
#                     linestringlist=[line.coords[i]]
#                else:
#                     linestringlist.append(line.coords[i])
#
#                     if i+1 == len(line.coords)-1:
#                        linestringlist.append(line.coords[i+1])
#                        geometry.append(shapely.LineString(linestringlist))
#                i += 1
#
#            
#
#
#    else:
#        linestringlist=[stroke_gdf.geometry[j].coords[0]]
#
#        i=1
#        while i != len(stroke_gdf.geometry[j].coords)-1:
#            a= stroke_gdf.geometry[j].coords[i-1]
#            b = stroke_gdf.geometry[j].coords[i]
#            c = stroke_gdf.geometry[j].coords[i+1]
#            angle1 = math.degrees(math.atan2(a[1] -b[1], a[0]-b[0]))
#            angle2= math.degrees(math.atan2(b[1] -c[1], b[0]-c[0]))
#
#
#            if abs(angle1-angle2) > 45:
#                 linestringlist.append(stroke_gdf.geometry[j].coords[i])
#                 geometry.append(shapely.LineString(linestringlist))
#                 linestringlist=[stroke_gdf.geometry[j].coords[i]]
#            else:
#                 linestringlist.append(stroke_gdf.geometry[j].coords[i])
#
#                 if i+1 == len(stroke_gdf.geometry[j].coords)-1:
#                    linestringlist.append(stroke_gdf.geometry[j].coords[i+1])
#                    geometry.append(shapely.LineString(linestringlist))
#            i += 1




#s= gpd.GeoSeries(geometry)
#direction=[]
#final_gdf = gpd.GeoDataFrame(geometry=s)
#for line in s:
#    bearing = math.degrees(math.atan2(line.coords[0][1] -line.coords[-1][1], line.coords[0][0]-line.coords[-1][0]))
#    if 17<= bearing <= 107 or -163 <= bearing <= -73:
#        direction.append(1)
#
#    else:
#        direction.append(0)
#
#    
#final_gdf["directionality"]= direction
#
#final_df= pd.DataFrame(final_gdf)
#
#NS= final_df.loc[final_df["directionality"]==1]
#EW= final_df.loc[final_df["directionality"]==0]
#
#NS_gdf= gpd.GeoDataFrame(NS,geometry=NS["geometry"])
#EW_gdf= gpd.GeoDataFrame(EW,geometry=EW["geometry"])





#NS_gdf.to_file('NS.gpkg', driver='GPKG', layer="NS" ) 
#EW_gdf.to_file('EW.gpkg', driver='GPKG', layer="EW" ) 
#
#final_gdf.plot(final_gdf.directionality,
#               figsize=(15, 15),
#                cmap="viridis",
#                linewidth=.5,
#                scheme="headtailbreaks",
#                legend= True
#               ).set_axis_off()
#plt.show()





#number_list=[]
#for i in range(5):
#[]
#        number = random.randint(0, len(nodes)-1)
#
#        if number in number_list:
#            number = random.randint(0, len(nodes)-1)
#        else :
#            number_list.append(number)
#
#OD = nodes.iloc[number_list]
#
#origin = random.randint(0,len(OD)-1)
#destination = random.randint(0,len(OD)-1)
#while origin == destination:
#    destination = random.randint(0,len(OD)-1)
#origin = OD.iloc[origin]
#destination = OD.iloc[destination]
#acid = "drone"+str(random.randint(0,500))
#shortest_path = ox.distance.shortest_path(Garment,origin.name,destination.name)
#print(shortest_path)
#print(nodes)
#for x in shortest_path:
#     print(nodes.loc[x][0])
#     print(x)
#     print("------------------------------------------")
#
#print(type(shortest_path))


#bs.traffic.create(acid, "DJI Matrice 200", origin[1], origin[0])

