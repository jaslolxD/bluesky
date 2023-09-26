import bluesky as bs
from bluesky import stack 
from bluesky.traffic import Route
from bluesky.core import Entity, timed_function
from bluesky.stack import command
from bluesky.tools.aero import kts, ft, nm
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
        self.target_ntraf = 1
        self.traf_id = 1
        self.traf_spd = 10
        self.traf_alt = 100 * ft
        with self.settrafarrays():
            self.route_edges = []
        return
    
    def create(self, n=1):
        super().create(n)
        # Store creation time of new aircraft
        self.route_edges[-n:] = [0]*n # Default edge


    def loadCity(self):
        graph = ox.load_graphml(filepath=r"C:\Users\Jason\Documents\Thesis\Network data\G_final.graphml")
        nodes, edges = ox.graph_to_gdfs(graph)
        return graph, nodes, edges
    
    def loadRoutes(self):
        routes = os.listdir(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles')
        return routes

    @timed_function(dt = 1)
    def spawn(self):
        routes = os.listdir(f'C:/Coding/bluesky/bluesky/plugins/graph_genetic_algorithm/pickles')
        random.seed(1)
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
                print(f"{future_angle} for WP{count}")
                count +=1

            acrte.calcfp()
            stack.stack(f"DIRECT {acid} WP0")
            stack.stack(f'LNAV {acid} ON')
            stack.stack(f'VNAV {acid} ON')

    @timed_function(dt = 10)
    def route_checker(self):
        try:
            bs.traf.id
        except:
            return
        else:
            acids = bs.traf.id

        for acid in acids:
            time = 0
            acidx = bs.traf.id2idx(acid)
            acrte = Route._routes.get(acid)
            #print(acrte.getnextwp())
            #print(acrte.iactwp)
            #print(len(acrte.wpname))
            #print(acrte.wpdistto[acrte.iactwp])
            current_wp = acrte.iactwp
            first_run = True
            start_turn = False
            while time < 10:
                if first_run == True:
                    _, dist = kwikqdrdist(bs.traf.lat[acidx], bs.traf.lon[acidx], acrte.wplat[current_wp], acrte.wplon[current_wp])
                    dist *= nm

                    #Drone going towards a turn in the first run
                    if acrte.wpflyturn[current_wp] == True:
                        wpqdr, _ = kwikqdrdist(acrte.wplat[current_wp -1], acrte.wplon[current_wp -1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp], acrte.wplon[current_wp], acrte.wplat[current_wp +1], acrte.wplon[current_wp +1])
                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
                        accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
                    
                        if dist > turndist + accel_dist:
                            #Cruise distance
                            cruise_dist = dist - accel_dist - turndist 
                            cruise_time = cruise_dist / (15*kts)

                            #Deceleration time
                            accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #Turn  time times half cuz only till current_wp
                            turn_time = turning_dist * 0.5 / (5*kts)
                            start_turn = True

                            #Add it all up
                            time_diff = cruise_time + accel_time + turn_time
                            time += time_diff

                            bs.scr.echo(f"Initial turn Cruise region time: {time}")

                        elif dist > turndist:

                            #deceleration time
                            accel_time = abs(bs.traf.tas[acidx] - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #Turn time half cuz only till current_wp
                            turn_time = turning_dist * 0.5 / (5*kts)
                            start_turn = True

                            #Add it all up
                            time_diff = accel_time + turn_time
                            time += time_diff

                            bs.scr.echo(f"Initial turn Decell region time: {time}")

                        else:
                            turn_time = turning_dist * 0.5 / (5*kts)
                            time += 0.5 * turn_time

                            bs.scr.echo(f"Initiral Turn turning region time: {time}")



                    #Drone going away from a turn in the first run
                    elif acrte.wpflyturn[current_wp-1] == True:
                        wpqdr, _ = kwikqdrdist(acrte.wplat[current_wp -2], acrte.wplon[current_wp -2], acrte.wplat[current_wp-1], acrte.wplon[current_wp-1])
                        nextwpqdr, leg_dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        leg_dist = leg_dist *nm
                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
                        accel_dist = distaccel( 5*kts, 15*kts, bs.traf.perf.axmax[acidx])
                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
                        cruise_dist = leg_dist - accel_dist - turndist
                        

                        if dist < leg_dist - turndist - accel_dist:
                            turn_time = turning_dist * 0.5 / (5*kts)
                            time += 0.5 * turn_time

                        elif dist < accel_dist:
                            #acceleration time
                            accel_time = abs(bs.traf.tas[acidx] - 5*kts)/ bs.traf.perf.axmax[acidx]

                            time_diff = accel_time
                            time += time_diff

                        elif dist < accel_dist + cruise_dist:
                            #acceleration time
                            accel_time = abs(15* kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #cruise time
                            partial_cruise_dist = dist - accel_dist
                            cruise_time = partial_cruise_dist / (5*kts)

                            #Add it all up
                            time_diff = cruise_time + accel_time
                            time += time_diff

                        else: 
                            #acceleration time
                            accel_time = abs(15* kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #cruise time
                            cruise_time = cruise_dist / (5*kts)

                            #Turning time
                            turn_time = turning_dist * 0.5 * 0.5/ (5*kts)

                            #Add it all up
                            time_diff = cruise_time + accel_time + turn_time
                            time += time_diff
                            
                    #Regular cruise
                    else:
                        time += dist/ (15*kts)
                    #bs.scr.echo(f"Initial distance to waypoint {acrte.iactwp} is {dist}")
                    #bs.scr.echo(f"Time difference is {time}")
                    #bs.scr.echo("-------------------------------------------------------------------------------")
                    first_run = False
                    current_wp +=1

                #Iterations after turn
                elif start_turn == True:
                    if acrte.wpflyturn[current_wp] == True:
                        #second part of initial turn
                        initial_turn_time = turning_dist * 0.5 / (5*kts)
                        initial_turndist = turndist

                        #Calculations for the second turn parameters
                        wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -1], acrte.wplon[current_wp -1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        dist = dist *nm
                        nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp], acrte.wplon[current_wp], acrte.wplat[current_wp +1], acrte.wplon[current_wp +1])
                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)

                        #Calculate the leg distance, acceleration distance and turning distance (total distance covered by turn) for second turn
                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)

                        #Cruise distance with turning speed instead of cruise
                        cruise_dist = dist - turndist - initial_turndist
                        cruise_time = cruise_dist / (5*kts)

                        # Second turn time times half cuz only till current_wp
                        turn_time = turning_dist * 0.5 / (5*kts)
                        start_turn = True

                        #Total time
                        time_diff = initial_turn_time + cruise_time + turn_time
                        time += time_diff
                        
                        bs.scr.echo(f"Time difference between {current_wp -1} and {current_wp } is {time_diff}")
                        bs.scr.echo(f"turn time is {turn_time}")
                        bs.scr.echo(f"Cruise time is {cruise_time}")
                        bs.scr.echo(f"Accel time is {accel_time}")
                        bs.scr.echo(f"------------------------------------------------------------------------------------------------------")
                        
                        current_wp +=1


                    else:
                        #second part of turn
                        turn_time = turning_dist * 0.5 / (5*kts)

                        #Acceleration
                        accel_dist = distaccel(5*kts, 15*kts, bs.traf.perf.axmax[acidx])
                        accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                        #Cruise whilst still being in turning speed
                        _ , dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        dist = dist * nm
                        cruise_dist = dist - accel_dist - turndist
                        cruise_time = cruise_dist / (5*kts)

                        #Total time
                        time_diff = cruise_time + accel_time + turn_time
                        time += time_diff
                        
                        start_turn = False
                        current_wp +=1

                #Iterations after a regular leg
                else:
                    if acrte.wpflyturn[current_wp] == True:
                        wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -1], acrte.wplon[current_wp -1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        dist = dist *nm
                        nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp], acrte.wplon[current_wp], acrte.wplat[current_wp +1], acrte.wplon[current_wp +1])
                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
                        
                        #Calculate the leg distance, acceleration distance and turning distance (total distance covered by turn)
                        accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
                        
                        #Cruise distance
                        cruise_dist = dist - accel_dist - turndist 
                        cruise_time = cruise_dist / (15*kts)

                        #Deceleration time
                        accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                        #Turn  time times half cuz only till current_wp
                        turn_time = turning_dist * 0.5 / (5*kts)
                        start_turn = True

                        #Add it all up
                        time_diff = cruise_time + accel_time + turn_time
                        time += time_diff

                        bs.scr.echo(f"Total leg distance: {dist}")
                        bs.scr.echo(f"cruise time: {cruise_time}")
                        bs.scr.echo(f"cruise distance: {cruise_dist}")
                        bs.scr.echo(f"accel time: {accel_time}")
                        bs.scr.echo(f"Turning time: {turn_time}")

                        bs.scr.echo(f"Regular turn leg: {time_diff}")    
                        current_wp +=1
                    
                    else:
                        _ , dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        dist = dist *nm
                        time_diff = dist / (15*kts)
                        time += time_diff
                        #bs.scr.echo(f"Time difference between {current_wp -1} and {current_wp } is {time_diff}")
                        #bs.scr.echo(f"Distance travelled is {dist}m")
                        #bs.scr.echo(f"First Lat Lon {acrte.wplat[current_wp -1]} , {acrte.wplon[current_wp-1]}")
                        #bs.scr.echo(f"Final Lat Lon {acrte.wplat[current_wp]} , {acrte.wplon[current_wp]}")
                        #bs.scr.echo(f"-------------------------------------------------------------------------------------------")
                        #
                        #print(f"Time difference between {current_wp -1} and {current_wp } is {time_diff}")                        
                        #print(f"Distance travelled is {dist}m")
                        #print(f"First Lat Lon {acrte.wplat[current_wp -1]} , {acrte.wplon[current_wp -1]}")                        
                        #print(f"Final Lat Lon {acrte.wplat[current_wp]} , {acrte.wplon[current_wp]}")
                        #print(f"-------------------------------------------------------------------------------------------") 
                        bs.scr.echo(f"Regular leg: {time_diff}")                       
                        current_wp +=1


            #if acrte.wpflyturn[current_wp-1] == True:
            #    overshoot_time = time-10
            #    bearing , dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
            #    if overshoot_time < turn_time:
            #        turn_position_lat, turn_position_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, turndist)
            #        time_in_turn = turn_time - overshoot_time
#
#
#
            #    elif overshoot_time < turn_time+accel_time:
#
            #    else:
#
#
            #    
            #elif acrte.wpflyturn[current_wp-2] == True:
            #    
#
            #else:
            #    overshoot_time = time-10
            #    overshoot_dist = overshoot_time * 15*kts
            #    bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
            #    lat, lon = kwikpos(acrte.wplat[current_wp], acrte.wplon[current_wp], bearing, overshoot_dist/nm)

            #Print stuff
            #bs.scr.echo(f"Current location: {bs.traf.lat[acidx]} {bs.traf.lon[acidx]}")
            #bs.scr.echo(f"Predicted location: {lat} {lon}")
            #bs.scr.echo(f"Overshoot dist {overshoot_dist}")
            #bs.scr.echo(f"Bearing {bearing}")
            bs.scr.echo(f"Going to waypoint now: {acrte.iactwp}")
            bs.scr.echo(f"Waypoint predicted: {current_wp -1}")
            #bs.scr.echo(f"Next turn distance {bs.traf.actwp.turndist[acidx]}")
            #bs.scr.echo(f"Turnadius {bs.traf.actwp.nextturnrad[acidx]}")
            #bs.scr.echo(f"Turn wp index {bs.traf.actwp.nextturnidx[acidx]}")
            #bs.scr.echo(f"Turn Distance {turndist}")
            #bs.scr.echo(f"Turn Radius {turnrad}")
            #bs.scr.echo(f"inital angle is {wpqdr}")
            #bs.scr.echo(f"second angle is {nextwpqdr}")
            stack.stack(f"HOLD")

#    @timed_function(dt = 1)
#    def printer(self):
#        bs.scr.echo(f"")          
    

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
                stack.stack(f'DEL {acid}')


    def reset(self):
        self.graph , self.nodes, self.edges = self.loadCity()
        self.target_ntraf = 1
        self.traf_id = 1
        self.traf_spd = 20
        self.traf_alt = 100 * ft

    
def distaccel(v0,v1,axabs):
    """Calculate distance travelled during acceleration/deceleration
    v0 = start speed, v1 = endspeed, axabs = magnitude of accel/decel
    accel/decel is detemremind by sign of v1-v0
    axabs is acceleration/deceleration of which absolute value will be used
    solve for x: x = vo*t + 1/2*a*t*t    v = v0 + a*t """
    return 0.5*np.abs(v1*v1-v0*v0)/np.maximum(.001,np.abs(axabs))