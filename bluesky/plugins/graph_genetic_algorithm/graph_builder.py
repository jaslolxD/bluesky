import osmnx as ox
import geopandas as gpd
from os import path
import numpy as np
import shapely
import pandas as pd

class GraphBuilder():
    def __init__(self, gis_data_path, direction_0_name, direction_1_name):
        # load graph direction 0
        self.G_0 = ox.load_graphml(filepath=path.join(gis_data_path, direction_0_name), node_dtypes={"y" : float,
                                                                                                     "x" : float,
                                                                                                     "lon" : float,
                                                                                                     "lat" : float,
                                                                                                     "geometry": shapely.geometry.point.Point})

        # get gdfs of dirextion 0
        self.nodes, self.edges_0 = ox.graph_to_gdfs(self.G_0)

        # load graph direction 1
        self.G_1 = ox.load_graphml(filepath=path.join(gis_data_path, direction_1_name))

        # get gdfs of dirextion 1
        _, self.edges_1 = ox.graph_to_gdfs(self.G_1)

        # create master dictionary with each group split
        self.create_builder_dict()

    def create_builder_dict(self):

        # first do a sanity check. check if both directions have the same number of groups
        all_stroke_groups_0 = np.sort(np.array(self.edges_0.loc[:,'stroke_group']).astype(np.int32))
        all_stroke_groups_1 = np.sort(np.array(self.edges_1.loc[:,'stroke_group']).astype(np.int32))

        if not np.array_equal(all_stroke_groups_0, all_stroke_groups_1):
            print('The two graphs do not have the same stroke_group numbers')

        
        # now loop through all stroke_groups and create the master graph builder
        self.stroke_groups = np.sort(np.unique(np.array(self.edges_0.loc[:,'stroke_group']).astype(np.int32)))

        self.graph_builder_dict = dict()
        for stroke_group in self.stroke_groups:

            # get gdf of edges_0
            edges_in_group_0 = self.edges_0.loc[self.edges_0['stroke_group']== str(stroke_group)]

            # get gdf of edges_1
            edges_in_group_1 = self.edges_1.loc[self.edges_1['stroke_group']== str(stroke_group)]
            
            # create master dictionary
            self.graph_builder_dict[stroke_group] = {0: edges_in_group_0, 1: edges_in_group_1}
    
    def build_graph(self, direction_list):
        """graph builder

        Args:
            dir_list (list): list with booleans. each value represents group
        """        

        # firs check that dir list is equal in length to stroke group
        if len(self.stroke_groups) != len(direction_list):
            print('Incompatible direction list and stroke groups!!!!!!!')
            print('len(direction_list) must equal len(self.stroke_groups)!!!!!!!!')
            return
        
        # now initiate a geodataframe
        edge_gdf = gpd.GeoDataFrame()
        for stroke_group, graph_choice in enumerate(direction_list):
            curr_gdf = self.graph_builder_dict[stroke_group][graph_choice]
            edge_gdf = pd.concat([edge_gdf,curr_gdf])
        
        # set correct crs
        edge_gdf = edge_gdf.set_crs(self.edges_0.crs)

        graph = ox.graph_from_gdfs(self.nodes, edge_gdf)

        return graph