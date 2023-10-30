import bluesky as bs
from bluesky import stack 
from bluesky.traffic import Route
from bluesky.core import Entity, timed_function
from bluesky.stack import command
from bluesky.tools.aero import kts, ft, nm, fpm
from bluesky.tools.geo import kwikqdrdist, kwikpos
from bluesky.tools.misc import degto180
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import random
import pickle
import os
import numpy as np

def init_plugin():
    # Configuration parameters
    config = {
        'plugin_name': 'TRAFFICSPAWNER',
        'plugin_type': 'sim',
        'reset': reset
    }
    # Put TrafficSpawner in bs.traf
    bs.traf.TrafficSpawner = trafficSpawner()
    bs.stack.stack(f'SCHEDULE 00:00:00 PAN 40.776676,-73.971321')
    bs.stack.stack(f'SCHEDULE 00:00:00 ZOOM 5')
    print("hi init")
    return config

def reset():
    bs.traf.TrafficSpawner.reset()



class trafficSpawner(Entity):
    def __init__(self):
        super().__init__()
        self.graph , self.nodes, self.edges = self.loadCity()
        self.target_ntraf = 20
        self.traf_id = 1
        self.traf_spd = 10
        self.traf_alt = 100 * ft

        # Logging related stuff

        self.prevconfpairs = set()

        self.prevlospairs = set()

        self.confinside_all = 0

        self.deleted_aircraft = 0

        self.losmindist = dict()

        

        with self.settrafarrays():

            self.route_edges = []

            # Metrics

            self.distance2D = np.array([])

            self.distance3D = np.array([])

            self.distancealt = np.array([])

            self.create_time = np.array([])

        return



    def loadCity(self):
        graph = ox.load_graphml(filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_final.graphml")
        nodes, edges = ox.graph_to_gdfs(graph)
        return graph, nodes, edges
    
    def loadRoutes(self):
        routes = os.listdir(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles')
        return routes
        

    @timed_function(dt = 1)
    def spawn(self):
        routes = os.listdir(f'C:/Coding/bluesky_fork2/bluesky/plugins/graph_genetic_algorithm/pickles')
        #random.seed(1)
        while bs.traf.ntraf < self.target_ntraf:
            count = 0
            route_entry = random.randint(0,len(routes)-1)
            filename = routes[route_entry]
            route = pd.read_pickle(f'C:/Coding/bluesky_fork2/bluesky/plugins/graph_genetic_algorithm/pickles/{filename}')
            lats, lons = zip(*route)

            acid = f"DR{self.traf_id}"
            self.traf_id += 1
            actype = "M600"
            achdg , _ = kwikqdrdist(lats[0], lons[0], lats[1], lons[1])
            bs.traf.cre(acid, actype, lats[0], lons[0], achdg, self.traf_alt, 15 *kts)

            acrte = Route._routes.get(acid)
            acidx = bs.traf.id.index(acid)
            bs.scr.echo(f"spawning")

            lastwp=[]
            for i in range(len(route)):
                if i == len(route)-1:
                    acrte.swflyby = True
                    acrte.swflyturn = False
                    wptype = Route.wplatlon
                    acrte.addwpt_simple(acidx,f"WP{count}", wptype, route[i][0], route[i][1], self.traf_alt, 15*kts)
                elif i == 0:
                    future_angle = achdg
                    acrte.swflyby = True
                    acrte.swflyturn = False
                    wptype = Route.wplatlon
                    acrte.addwpt_simple(acidx,f"WP{count}", wptype, route[i][0], route[i][1], self.traf_alt, 15*kts)
                else: 
                    future_angle, _ = kwikqdrdist(route[i][0], route[i][1], route[i+1][0], route[i+1][1])
                    if abs(current_angle - future_angle) > 50:
                        acrte.swflyby = False
                        acrte.swflyturn = True
                        acrte.turnspd = 5 * kts
                        wptype = Route.wplatlon
                        acrte.addwpt_simple(acidx,f"WP{count}", wptype, route[i][0], route[i][1], self.traf_alt, 5*kts)
                    else:
                        acrte.swflyby = True
                        acrte.swflyturn = False
                        wptype = Route.wplatlon
                        acrte.addwpt_simple(acidx,f"WP{count}", wptype, route[i][0], route[i][1], self.traf_alt, 15*kts)

                current_angle = future_angle
                count +=1

            acrte.calcfp()
            stack.stack(f"DIRECT {acid} WP0")
            stack.stack(f'LNAV {acid} ON')
            stack.stack(f'VNAV {acid} ON')


    #@timed_function(dt = 10)
    def printer(self):
        try:
            bs.traf.id
        except:
            bs.scr.echo("this doesnt work")
            return
        else:
            acids = bs.traf.id

        for acid in acids:
            time = 0
            acidx = bs.traf.id2idx(acid)
            acrte = Route._routes.get(acid)

            bs.scr.echo(f" lat: {bs.traf.lat[acidx]} lon: {bs.traf.lon[acidx]}")

        stack.stack("HOLD")

    

    

    @timed_function(dt = 0.5)
    def delete_aircraft(self):
        # Delete aircraft that have LNAV off and have gone past the last waypoint.
        lnav_on = bs.traf.swlnav
        still_going_to_dest = np.logical_and(abs(degto180(bs.traf.trk - bs.traf.ap.qdr2wp)) < 10.0, 
                                       bs.traf.ap.dist2wp > 5)
        delete_array = np.logical_and.reduce((np.logical_not(lnav_on), 
                                         bs.traf.actwp.swlastwp,
                                         np.logical_not(still_going_to_dest)))
        
        if np.any(delete_array):
            # Get the ACIDs of the aircraft to delete
            acids_to_delete = np.array(bs.traf.id)[delete_array]
            for acid in acids_to_delete:
                idx = bs.traf.id2idx(acid)
                bs.traf.CDLogger.flst.log(
                acid,
                self.create_time[idx],
                bs.sim.simt - self.create_time[idx],
                (self.distance2D[idx]),
                (self.distance3D[idx]),
                (self.distancealt[idx]),
                bs.traf.lat[idx],
                bs.traf.lon[idx],
                bs.traf.alt[idx]/ft,
                bs.traf.tas[idx]/kts,
                bs.traf.vs[idx]/fpm,
                bs.traf.hdg[idx],
                bs.traf.cr.active[idx],
                bs.traf.aporasas.alt[idx]/ft,
                bs.traf.aporasas.tas[idx]/kts,
                bs.traf.aporasas.vs[idx]/fpm,
                bs.traf.aporasas.hdg[idx])
                bs.traf.delete(idx)
                #stack.stack(f'DEL {acid}')


    def reset(self):
        self.graph , self.nodes, self.edges = self.loadCity()
        self.target_ntraf = 1
        self.traf_id = 1
        self.traf_spd = 20
        self.traf_alt = 100 * ft

        # Logging related stuff

        self.prevconfpairs = set()

        self.prevlospairs = set()

        self.confinside_all = 0

        self.deleted_aircraft = 0

        self.losmindist = dict()

        

        with self.settrafarrays():

            self.route_edges = []

            # Metrics

            self.distance2D = np.array([])

            self.distance3D = np.array([])

            self.distancealt = np.array([])

            self.create_time = np.array([])

        return

    
def distaccel(v0,v1,axabs):
    """Calculate distance travelled during acceleration/deceleration
    v0 = start speed, v1 = endspeed, axabs = magnitude of accel/decel
    accel/decel is detemremind by sign of v1-v0
    axabs is acceleration/deceleration of which absolute value will be used
    solve for x: x = vo*t + 1/2*a*t*t    v = v0 + a*t """
    return 0.5*np.abs(v1*v1-v0*v0)/np.maximum(.001,np.abs(axabs))