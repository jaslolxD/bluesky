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
import numpy as np
from bluesky.traffic.asas import ConflictDetection
from bluesky.tools import geo, datalog


def init_plugin():
    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'JASONCD',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim'
    }

    return config

confheader = \
    '#######################################################\n' + \
    'CONF LOG\n' + \
    'Conflict Statistics\n' + \
    '#######################################################\n\n' + \
    'Parameters [Units]:\n' + \
    'Simulation time [s], ' + \
    'Unique CONF ID [-]' + \
    'ACID1 [-],' + \
    'ACID2 [-],' + \
    'LAT1 [deg],' + \
    'LON1 [deg],' + \
    'ALT1 [ft],' + \
    'LAT2 [deg],' + \
    'LON2 [deg],' + \
    'ALT2 [ft]\n'

uniqueconflosheader = \
    '#######################################################\n' + \
    'Unique CONF LOS LOG\n' + \
    'Shows whether unique conflicts results in a LOS\n' + \
    '#######################################################\n\n' + \
    'Parameters [Units]:\n' + \
    'Unique CONF ID, ' + \
    'Resulted in LOS\n'

class JasonCD(ConflictDetection):
    def __init__(self):
        super().__init__()
        # New detection parameters
        self.predicted_waypoints = [] # Predicted list of waypoints
        self.qdr_mat = np.array([]) # QDR for all aircraft
        self.dist_mat = np.array([]) # Distance for all aircraft
        self.dtlookahead_def = 30
        self.measurement_freq = 5
        self.rpz_def = 50
        
        # Logging
        self.conflictlog = datalog.crelog('CDR_CONFLICTLOG', None, confheader)
        self.uniqueconfloslog = datalog.crelog('CDR_WASLOSLOG', None, uniqueconflosheader)
        
        # Conflict related

        self.prevconfpairs = set()

        self.prevlospairs = set()

        self.unique_conf_dict = dict()

        self.counter2id = dict() # Keep track of the other way around

        self.unique_conf_id_counter = 0 # Start from 0, go up
        

    def reset(self):
        super().reset()
        # Reset the things
        self.predicted_waypoints = [] # Predicted list of waypoints
        self.qdr_mat = np.array([]) # QDR for all aircraft
        self.dist_mat = np.array([]) # Distance for all aircraft

        # Conflict related

        self.prevconfpairs = set()

        self.prevlospairs = set()

        self.unique_conf_dict = dict()

        self.counter2id = dict() # Keep track of the other way around

        self.unique_conf_id_counter = 0 # Start from 0, go up

    
    def clearconfdb(self):
        return super().clearconfdb()
    
    def update(self, ownship, intruder):
        ''' Perform an update step of the Conflict Detection implementation. '''
        self.confpairs, self.inconf = \
                self.detect(ownship, intruder, self.rpz_def, self.hpz, self.dtlookahead_def)

        # confpairs has conflicts observed from both sides (a, b) and (b, a)
        # confpairs_unique keeps only one of these
        confpairs_unique = {frozenset(pair) for pair in self.confpairs}
        #lospairs_unique = {frozenset(pair) for pair in self.lospairs}

        self.confpairs_all.extend(confpairs_unique - self.confpairs_unique)
        #self.lospairs_all.extend(lospairs_unique - self.lospairs_unique)

        # Update confpairs_unique and lospairs_unique
        self.confpairs_unique = confpairs_unique
        #self.lospairs_unique = lospairs_unique
        
        # Update the logging
        self.update_log()
    
    def detect(self, ownship, intruder, rpz, hpz, dtlookahead):
        # Do state-based detection for LOS information
        #confpairs_s, lospairs_s, inconf_s, tcpamax_s, qdr_s, \
        #    dist_s, dcpa_s, tcpa_s, tLOS_s, qdr_mat, dist_mat = \
        #        self.sb_detect(ownship, intruder, self.rpz_def, self.hpz, self.dtlookahead_def)    
                
        # Save the qdr_mat and dist_mat, the matrices that have the information about all aircraft
        #self.qdr_mat = qdr_mat
        #self.dist_mat = dist_mat 
                
        # Do the own detection
        confpairs, inconf, self.predicted_waypoints = self.jason_detect(ownship, intruder, self.rpz_def, self.hpz, self.dtlookahead_def)

        array = self.traj_detect(ownship, intruder, self.rpz_def, self.dtlookahead_def, self.measurement_freq)

        return confpairs, inconf
    
    def jason_detect(self, ownship, intruder, rpz, hpz, dtlookahead):
        # All aircraft are within 300m of each other are in conflict!! (definitely change this)
        confpairs_idx = np.array(np.where(self.dist_mat<300)).T
        # These are aircraft IDXs though, and BlueSky likes its confpairs in ACIDs, so convert them.
        confpairs_acid = [(bs.traf.id[idx1], bs.traf.id[idx2]) for idx1, idx2 in confpairs_idx]
        # Set the flag for the aircraft that are in confpairs to 1
        inconf = np.zeros(bs.traf.ntraf)
        for idx1, idx2 in confpairs_idx:
            inconf[idx1] = 1
        
        # Empty prediction for now
        predicted_waypoints = []
        
        return confpairs_acid, inconf, predicted_waypoints
    
    def traj_detect(self,ownship, intruder, rpz, dtlookahead, measurement_freq):
        try:
            bs.traf.id
        except:
            bs.scr.echo("this doesnt work")
            return
        else:
            acids = bs.traf.id

        array_measurement= []
        for acid in acids:
            time = 0
            acidx = bs.traf.id2idx(acid)
            acrte = Route._routes.get(acid)
            current_wp = acrte.iactwp
            first_run = True
            start_turn = False
            floor_div = 0
            rpz = 50
            while time < 30:
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

                            #No turn time since turn is made for the second waypoint
                            start_turn = True

                            #Add it all up
                            time_diff = cruise_time + accel_time
                            time += time_diff
                            
                            current_wp +=1
                            first_run = False

                            #bs.scr.echo(f"Initial turn Cruise region time: {time}")

                        else:

                            #deceleration time
                            accel_time = abs(bs.traf.tas[acidx] - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #Turn time half cuz only till current_wp
                            start_turn = True

                            #Add it all up
                            time_diff = accel_time
                            time += time_diff

                            current_wp +=1
                            first_run = False

                            #bs.scr.echo(f"Initial turn Decell region time: {time}")


                    #Drone going away from a turn in the first run
                    elif acrte.wpflyturn[current_wp-1] == True:
                        wpqdr, _ = kwikqdrdist(acrte.wplat[current_wp -2], acrte.wplon[current_wp -2], acrte.wplat[current_wp-1], acrte.wplon[current_wp-1])
                        nextwpqdr, leg_dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        leg_dist = leg_dist *nm
                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
                        accel_dist = distaccel( 5*kts, 15*kts, bs.traf.perf.axmax[acidx])
                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
                        cruise_dist = leg_dist - accel_dist - turndist
                        

                        if dist < accel_dist:
                            #acceleration time
                            accel_time = abs(bs.traf.tas[acidx] - 15*kts)/ bs.traf.perf.axmax[acidx]

                            time_diff = accel_time
                            time += time_diff

                            current_wp +=1
                            first_run = False

                        elif dist < accel_dist + cruise_dist:
                            #acceleration time
                            accel_time = abs(15* kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #cruise time
                            partial_cruise_dist = dist - accel_dist
                            cruise_time = partial_cruise_dist / (5*kts)

                            #Add it all up
                            time_diff = cruise_time + accel_time
                            time += time_diff

                            current_wp +=1
                            first_run = False

                        else: 
                            #acceleration time
                            accel_time = abs(15* kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #cruise time
                            cruise_time = cruise_dist / (5*kts)

                            #Turning time
                            turn_time = turning_dist * 0.5/ (5*kts)

                            #Add it all up
                            time_diff = cruise_time + accel_time + turn_time
                            time += time_diff

                            current_wp +=1
                            first_run = False
                            
                    #Regular cruise
                    else:
                        time += dist/ (15*kts)
                        first_run = False
                        current_wp +=1

                    

                #Iterations after turn
                elif start_turn == True:
                    if acrte.wpflyturn[current_wp] == True:
                        #second part of initial turn
                        initial_turn_time = turning_dist/ (5*kts)
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
                        start_turn = True

                        #Total time
                        time_diff = initial_turn_time + cruise_time 
                        time += time_diff
                        
                        current_wp +=1


                    else:
                        #The turn
                        turn_time = turning_dist/ (5*kts)

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
                        start_turn = True

                        #Add it all up
                        time_diff = cruise_time + accel_time
                        time += time_diff
  
                        current_wp +=1
                    
                    else:
                        _ , dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
                        dist = dist *nm
                        time_diff = dist / (15*kts)
                        time += time_diff                    
                        current_wp +=1

        #--------------------------------------------------------------------------------------------------------------------------------------------------
            #Position Calculations
                if floor_div < time // measurement_freq:
                    i= 0
                    value = int(time // measurement_freq) - floor_div
                    while i < value and floor_div < dtlookahead / measurement_freq:
                        floor_div += 1
                        overshoot_time = time - floor_div * measurement_freq
                        #print(f"overshoot_time: {overshoot_time}")
                        #print(f"floor_div: {floor_div}")
                        #print(i)
                        print(current_wp -1)
                        print(acrte.wpname)

                        if acrte.wpflyturn[current_wp-1] == True:
                            wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -2], acrte.wplon[current_wp -2], acrte.wplat[current_wp-1], acrte.wplon[current_wp-1])
                            dist = dist *nm
                            nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp ], acrte.wplon[current_wp])
                            turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)

                            accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
                            accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                            #Ends in deceleration part before turn
                            if overshoot_time < accel_time:
                                overshoot_dist = 0.5 * bs.traf.perf.axmax[acidx] * (overshoot_time)**2 + 5 * kts * overshoot_time
                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)

                            #Ends in cruise part before turn
                            else: 
                                remaining_time = overshoot_time - accel_time
                                overshoot_dist = accel_dist + remaining_time * 15*kts
                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)



                        elif acrte.wpflyturn[current_wp-2] == True:
                            wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -3], acrte.wplon[current_wp -3], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
                            dist = dist *nm
                            nextwpqdr, leg_dist = kwikqdrdist(acrte.wplat[current_wp-2], acrte.wplon[current_wp-2], acrte.wplat[current_wp-1], acrte.wplon[current_wp-1])
                            leg_dist *= nm
                            turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)

                            accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
                            accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]

                            cruise_dist = leg_dist - turndist - accel_dist
                            cruise_time = cruise_dist / 5 *kts

                            if overshoot_time < accel_time:
                                overshoot_dist = - 0.5 * bs.traf.perf.axmax[acidx] * (overshoot_time)**2 + 15 * kts * overshoot_time
                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)

                            elif overshoot_time < accel_time + cruise_time:
                                remaining_time = overshoot_time - accel_time
                                overshoot_dist = accel_dist + remaining_time * 5*kts
                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)


                            else:
                                final_lat = acrte.wplat[current_wp -2]
                                final_lon = acrte.wplon[current_wp -2]


                        else:
                            overshoot_dist = overshoot_time * 15*kts
                            if acrte.wplat[current_wp-1] == acrte.wplat[current_wp-2]:
                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bs.traf.lat[acidx], bs.traf.lon[acidx])
                            else:
                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
                            final_lat, final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)

                            

                        #Data record
                        #print(f"{acid} , {final_lat}")
                        array_measurement.append([acid, floor_div, final_lat, final_lon])
                        i +=1

                try:
                    acrte.wpflyturn[current_wp]
                except:
                    break

          
        #print(array_measurement)

        confpairs =[]
        df = pd.DataFrame(array_measurement, columns=["acid", "part", "lat", "lon"])
        #print(df)

        try:
            parts = max(df["part"])
        except:
            print("No more tings")
        else:
            parts = max(df["part"])

            for i in range(1, parts+1):
                qdr,dist = geo.kwikqdrdist_matrix(np.asmatrix(df[df["part"] ==i ].lat),np.asmatrix(df[df["part"] ==i ].lon), np.asmatrix(df[df["part"] ==i ].lat), np.asmatrix(df[df["part"] ==i ].lon))
                I = np.eye(len(df[df["part"] ==i]["acid"].unique()))
                qdr = np.asarray(qdr)
                dist = np.asarray(dist) * nm + 1e9 * I
                #print(dist)
                conflicts = np.column_stack(np.where(dist < rpz))
                for pair in conflicts:
                    conflictpair = (df["acid"].unique()[pair[0]], df["acid"].unique()[pair[1]])
                    if conflictpair not in confpairs:
                        confpairs.append(conflictpair)

        #Conflict Pairs
        #print(confpairs)
        bs.scr.echo(f"{confpairs}")
        self.confpairs = confpairs
        confpairs_idx = [(bs.traf.id2idx(acid1), bs.traf.id2idx(acid2)) for acid1, acid2 in confpairs]

        inconf = np.zeros(bs.traf.ntraf)
        for idx1, idx2 in confpairs_idx:
            inconf[idx1] = 1

        self.inconf = inconf

        #LoS Pairs
        I = np.eye(ownship.ntraf)
        _, dist_state = qdr, dist = geo.kwikqdrdist_matrix(np.asmatrix(ownship.lat), np.asmatrix(ownship.lon),
                                    np.asmatrix(intruder.lat), np.asmatrix(intruder.lon))
        dist_state = np.asarray(dist_state) * nm + 1e9 * I
        swlos = (dist_state < rpz)
        lospairs = [(ownship.id[i], ownship.id[j]) for i, j in zip(*np.where(swlos))]
        #bs.scr.echo(f"{lospairs}")
        self.lospairs = lospairs
        

        return array_measurement
        
    def sb_detect(self, ownship, intruder, rpz, hpz, dtlookahead):
        ''' State-based detection.'''
        # Identity matrix of order ntraf: avoid ownship-ownship detected conflicts
        I = np.eye(ownship.ntraf)

        # Horizontal conflict ------------------------------------------------------

        # qdrlst is for [i,j] qdr from i to j, from perception of ADSB and own coordinates
        qdr, dist = geo.kwikqdrdist_matrix(np.asmatrix(ownship.lat), np.asmatrix(ownship.lon),
                                    np.asmatrix(intruder.lat), np.asmatrix(intruder.lon))
        

        # Convert back to array to allow element-wise array multiplications later on
        # Convert to meters and add large value to own/own pairs
        qdr = np.asarray(qdr)
        dist = np.asarray(dist) * nm + 1e9 * I

        # Calculate horizontal closest point of approach (CPA)
        qdrrad = np.radians(qdr)
        dx = dist * np.sin(qdrrad)  # is pos j rel to i
        dy = dist * np.cos(qdrrad)  # is pos j rel to i

        # Ownship track angle and speed
        owntrkrad = np.radians(ownship.trk)
        ownu = ownship.gs * np.sin(owntrkrad).reshape((1, ownship.ntraf))  # m/s
        ownv = ownship.gs * np.cos(owntrkrad).reshape((1, ownship.ntraf))  # m/s

        # Intruder track angle and speed
        inttrkrad = np.radians(intruder.trk)
        intu = intruder.gs * np.sin(inttrkrad).reshape((1, ownship.ntraf))  # m/s
        intv = intruder.gs * np.cos(inttrkrad).reshape((1, ownship.ntraf))  # m/s

        du = ownu - intu.T  # Speed du[i,j] is perceived eastern speed of i to j
        dv = ownv - intv.T  # Speed dv[i,j] is perceived northern speed of i to j

        dv2 = du * du + dv * dv
        dv2 = np.where(np.abs(dv2) < 1e-6, 1e-6, dv2)  # limit lower absolute value
        vrel = np.sqrt(dv2)

        tcpa = -(du * dx + dv * dy) / dv2 + 1e9 * I

        # Calculate distance^2 at CPA (minimum distance^2)
        dcpa2 = np.abs(dist * dist - tcpa * tcpa * dv2)

        # Check for horizontal conflict
        # RPZ can differ per aircraft, get the largest value per aircraft pair
        rpz = np.asarray(np.maximum(np.asmatrix(rpz), np.asmatrix(rpz).transpose()))
        R2 = rpz * rpz
        swhorconf = dcpa2 < R2  # conflict or not

        # Calculate times of entering and leaving horizontal conflict
        dxinhor = np.sqrt(np.maximum(0., R2 - dcpa2))  # half the distance travelled inzide zone
        dtinhor = dxinhor / vrel

        tinhor = np.where(swhorconf, tcpa - dtinhor, 1e8)  # Set very large if no conf
        touthor = np.where(swhorconf, tcpa + dtinhor, -1e8)  # set very large if no conf

        # Vertical conflict --------------------------------------------------------

        # Vertical crossing of disk (-dh,+dh)
        dalt = ownship.alt.reshape((1, ownship.ntraf)) - \
            intruder.alt.reshape((1, ownship.ntraf)).T  + 1e9 * I

        dvs = ownship.vs.reshape(1, ownship.ntraf) - \
            intruder.vs.reshape(1, ownship.ntraf).T
        dvs = np.where(np.abs(dvs) < 1e-6, 1e-6, dvs)  # prevent division by zero

        # Check for passing through each others zone
        # hPZ can differ per aircraft, get the largest value per aircraft pair
        hpz = np.asarray(np.maximum(np.asmatrix(hpz), np.asmatrix(hpz).transpose()))
        tcrosshi = (dalt + hpz) / -dvs
        tcrosslo = (dalt - hpz) / -dvs
        tinver = np.minimum(tcrosshi, tcrosslo)
        toutver = np.maximum(tcrosshi, tcrosslo)

        # Combine vertical and horizontal conflict----------------------------------
        tinconf = np.maximum(tinver, tinhor)
        toutconf = np.minimum(toutver, touthor)

        swconfl = np.array(swhorconf * (tinconf <= toutconf) * (toutconf > 0.0) *
                           np.asarray(tinconf < np.asmatrix(dtlookahead).T) * (1.0 - I), dtype=bool)

        # --------------------------------------------------------------------------
        # Update conflict lists
        # --------------------------------------------------------------------------
        # Ownship conflict flag and max tCPA
        inconf = np.any(swconfl, 1)
        tcpamax = np.max(tcpa * swconfl, 1)

        # Select conflicting pairs: each a/c gets their own record
        confpairs = [(ownship.id[i], ownship.id[j]) for i, j in zip(*np.where(swconfl))]
        swlos = (dist < rpz) * (np.abs(dalt) < hpz)
        lospairs = [(ownship.id[i], ownship.id[j]) for i, j in zip(*np.where(swlos))]

        return confpairs, lospairs, inconf, tcpamax, \
            qdr[swconfl], dist[swconfl], np.sqrt(dcpa2[swconfl]), \
                tcpa[swconfl], tinconf[swconfl], qdr, dist
    

    def update_log(self):
        '''Here, we are logging the information for current conflicts as well as
        whether these conflicts resulted in a LOS or not.'''
        confpairs_new = list(set(self.confpairs) - self.prevconfpairs) # New confpairs
        confpairs_out = list(self.prevconfpairs - set(self.confpairs)) # Pairs that are no longer in conflict
        lospairs_new = list(set(self.lospairs) - self.prevlospairs) # New lospairs
        
        # First of all, add the new conflicts to the unique dict tracker
        for confpair in confpairs_new:
            # The dict is of the following format:
            # lower_number_acidx_newer_number_acidx : [unique_id, was it a LOS or not]
            # First, get the aircraft IDX
            idx1 = bs.traf.id.index(confpair[0])
            idx2 = bs.traf.id.index(confpair[1])
            # Create dictionary entry
            if idx1 < idx2:
                dictkey = confpair[0] + confpair[1]
            else:
                dictkey = confpair[1] + confpair[0]
                
            if dictkey in self.unique_conf_dict:
                # Pair already in there
                continue
            else:
                self.unique_conf_dict[dictkey] = [self.unique_conf_id_counter, False]
                self.counter2id[self.unique_conf_id_counter] = dictkey 
                self.unique_conf_id_counter += 1
                
                self.conflictlog.log(
                self.unique_conf_dict[dictkey][0],
                confpair[0],
                confpair[1],
                bs.traf.lat[idx1],
                bs.traf.lon[idx1],
                bs.traf.alt[idx1],
                bs.traf.lat[idx2],
                bs.traf.lon[idx2],
                bs.traf.alt[idx2]
            )   
            
        # Now check the new LOS
        done_pairs = []
        for lospair in lospairs_new:
            # Set the los flag of these in the unique dict tracker
            idx1 = bs.traf.id.index(lospair[0])
            idx2 = bs.traf.id.index(lospair[1])
            if idx1 < idx2:
                dictkey = lospair[0] + lospair[1]
            else:
                dictkey = lospair[1] + lospair[0]
                
            if dictkey in done_pairs:
                # Already done, continue
                continue
            
            done_pairs.append(dictkey)
                
            # Set the bool as true
            if dictkey in self.unique_conf_dict:
                self.unique_conf_dict[dictkey][1] = True
            else:
                # This LOS was not detected, but it is usually because of weird geometry
                #print(dictkey)
                continue
                
            
        # Now handle aircraft that are no longer in confpairs
        done_pairs = []
        for confpair in confpairs_out:
            # There is a possibility that one aircraft thinks it is still in a conflict while the other
            # doesn't. If this confpair is still in confpairs but inverted, skip it
            if (confpair[1], confpair[0]) in self.confpairs:
                continue
            # Log these in the uniqueconfloslog
            if confpair[0] not in bs.traf.id or confpair[1] not in bs.traf.id:
                # One of these aircraft was deleted, so just log them and done.
                if confpair[0] + confpair[1] in self.unique_conf_dict:
                    dictkey = confpair[0] + confpair[1]
                elif confpair[1] + confpair[0] in self.unique_conf_dict:
                    dictkey = confpair[1] + confpair[0]
                else:
                    # Absolutely no clue, continue I guess
                    #print('huh')
                    continue
                
                self.uniqueconfloslog.log(
                self.unique_conf_dict[dictkey][0],
                str(self.unique_conf_dict[dictkey][1])
                )
                self.unique_conf_dict.pop(dictkey)
                continue
                    
                
            idx1 = bs.traf.id.index(confpair[0])
            idx2 = bs.traf.id.index(confpair[1])
            
            if idx1 < idx2:
                dictkey = confpair[0] + confpair[1]
            else:
                dictkey = confpair[1] + confpair[0]
                
            if dictkey in done_pairs:
                # Already done, continue
                continue
            
            done_pairs.append(dictkey)
            
            # We want to keep this entry for a few extra seconds and see what happens
            # Get the conflict info and log it, then delete the entry
            self.uniqueconfloslog.log(
                self.unique_conf_dict[dictkey][0],
                str(self.unique_conf_dict[dictkey][1])
            )
            self.unique_conf_dict.pop(dictkey)
        
        self.prevconfpairs = set(self.confpairs)
        self.prevlospairs = set(self.lospairs)


def distaccel(v0,v1,axabs):
    """Calculate distance travelled during acceleration/deceleration
    v0 = start speed, v1 = endspeed, axabs = magnitude of accel/decel
    accel/decel is detemremind by sign of v1-v0
    axabs is acceleration/deceleration of which absolute value will be used
    solve for x: x = vo*t + 1/2*a*t*t    v = v0 + a*t """
    return 0.5*np.abs(v1*v1-v0*v0)/np.maximum(.001,np.abs(axabs))