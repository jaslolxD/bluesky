import bluesky as bs
from bluesky import stack
from bluesky.traffic import Route
from bluesky.core import Entity, timed_function
from bluesky.stack import command
from bluesky.tools.aero import kts, ft, nm
from bluesky.tools.geo import kwikqdrdist, kwikpos, kwikdist
from bluesky.tools.misc import degto180
import shapely as sh
import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from bluesky.traffic.asas import ConflictDetection
from bluesky.tools import geo, datalog
from matplotlib.patches import Circle


def init_plugin():
    # Configuration parameters
    config = {
        # The name of your plugin
        "plugin_name": "JASONCD",
        # The type of this plugin. For now, only simulation plugins are possible.
        "plugin_type": "sim",
    }

    return config


confheader = (
    "#######################################################\n"
    + "CONF LOG\n"
    + "Conflict Statistics\n"
    + "#######################################################\n\n"
    + "Parameters [Units]:\n"
    + "Simulation time [s], "
    + "Unique CONF ID [-]"
    + "ACID1 [-],"
    + "ACID2 [-],"
    + "LAT1 [deg],"
    + "LON1 [deg],"
    + "ALT1 [ft],"
    + "LAT2 [deg],"
    + "LON2 [deg],"
    + "ALT2 [ft]\n"
)

uniqueconflosheader = (
    "#######################################################\n"
    + "Unique CONF LOS LOG\n"
    + "Shows whether unique conflicts results in a LOS\n"
    + "#######################################################\n\n"
    + "Parameters [Units]:\n"
    + "Unique CONF ID, "
    + "Resulted in LOS\n"
)


class JasonCD(ConflictDetection):
    def __init__(self):
        super().__init__()
        # New detection parameters
        self.dtlookahead_def = 30
        self.measurement_freq = 2
        self.rpz_def = 50
        self.plot_toggle = False
        self.df = []
        self.confinfo = []
        self.cruise_spd = 20 * kts

        # Logging
        self.conflictlog = datalog.crelog("CDR_CONFLICTLOG", None, confheader)
        self.uniqueconfloslog = datalog.crelog(
            "CDR_WASLOSLOG", None, uniqueconflosheader
        )

        # Conflict related

        self.prevconfpairs = set()

        self.prevlospairs = set()

        self.unique_conf_dict = dict()

        self.counter2id = dict()  # Keep track of the other way around

        self.unique_conf_id_counter = 0  # Start from 0, go up

    def reset(self):
        super().reset()
        # Reset the things
        self.dtlookahead_def = 30
        self.measurement_freq = 3
        self.rpz_def = 50
        self.plot_toggle = False
        self.df = []
        self.confinfo = []
        self.cruise_spd = 20 * kts

        # Logging
        self.conflictlog = datalog.crelog("CDR_CONFLICTLOG", None, confheader)
        self.uniqueconfloslog = datalog.crelog(
            "CDR_WASLOSLOG", None, uniqueconflosheader
        )

        # Conflict related
        self.prevconfpairs = set()
        self.prevlospairs = set()
        self.unique_conf_dict = dict()
        self.counter2id = dict()  # Keep track of the other way around
        self.unique_conf_id_counter = 0  # Start from 0, go up

    def clearconfdb(self):
        return super().clearconfdb()

    def update(self, ownship, intruder):
        """Perform an update step of the Conflict Detection implementation."""
        self.confpairs, self.inconf, self.lospairs, self.df, self.confinfo = self.detect(
            ownship, intruder, self.rpz_def, self.hpz, self.dtlookahead_def
        )

        # confpairs has conflicts observed from both sides (a, b) and (b, a)
        # confpairs_unique keeps only one of these
        confpairs_unique = {frozenset(pair) for pair in self.confpairs}
        lospairs_unique = {frozenset(pair) for pair in self.lospairs}

        self.confpairs_all.extend(confpairs_unique - self.confpairs_unique)
        self.lospairs_all.extend(lospairs_unique - self.lospairs_unique)

        # Update confpairs_unique and lospairs_unique
        self.confpairs_unique = confpairs_unique
        self.lospairs_unique = lospairs_unique

        # Update the logging
        self.update_log()

    def detect(self, ownship, intruder, rpz, hpz, dtlookahead):
        # Do state-based detection for LOS information
        # confpairs_s, lospairs_s, inconf_s, tcpamax_s, qdr_s, \
        #    dist_s, dcpa_s, tcpa_s, tLOS_s, qdr_mat, dist_mat = \
        #        self.sb_detect(ownship, intruder, self.rpz_def, self.hpz, self.dtlookahead_def)

        # Save the qdr_mat and dist_mat, the matrices that have the information about all aircraft
        # self.qdr_mat = qdr_mat
        # self.dist_mat = dist_mat

        # Do the own detection
        # confpairs, inconf, self.predicted_waypoints = self.jason_detect(ownship, intruder, self.rpz_def, self.hpz, self.dtlookahead_def)

        confpairs, inconf, lospairs, df, confinfo = self.traj_detect(
            ownship, intruder, self.rpz_def, self.dtlookahead_def, self.measurement_freq
        )

        return confpairs, inconf, lospairs, df, confinfo

    def jason_detect(self, ownship, intruder, rpz, hpz, dtlookahead):
        # All aircraft are within 300m of each other are in conflict!! (definitely change this)
        confpairs_idx = np.array(np.where(self.dist_mat < 300)).T
        # These are aircraft IDXs though, and BlueSky likes its confpairs in ACIDs, so convert them.
        confpairs_acid = [
            (bs.traf.id[idx1], bs.traf.id[idx2]) for idx1, idx2 in confpairs_idx
        ]
        # Set the flag for the aircraft that are in confpairs to 1
        inconf = np.zeros(bs.traf.ntraf)
        for idx1, idx2 in confpairs_idx:
            inconf[idx1] = 1

        # Empty prediction for now
        predicted_waypoints = []

        return confpairs_acid, inconf, predicted_waypoints

    def traj_detect(self, ownship, intruder, rpz, dtlookahead, measurement_freq):
        try:
            bs.traf.id
        except:
            #bs.scr.echo("this doesnt work")
            return
        else:
            acids = bs.traf.id

        array_measurement = []
        acid_conflicts = []
        for entry in bs.traf.cd.confpairs:
            acid_conflicts.append(entry[0])
            
        for acid in acids:
            time = 0
            acidx = bs.traf.id2idx(acid)
            acrte = Route._routes.get(acid)
            current_wp = acrte.iactwp
            first_run = True
            second_run = False
            start_turn = False
            floor_div = 0
            rpz = 50
            while time < self.dtlookahead_def:
                if first_run == True:
                    _, dist = kwikqdrdist(
                        bs.traf.lat[acidx],
                        bs.traf.lon[acidx],
                        acrte.wplat[current_wp],
                        acrte.wplon[current_wp],
                    )
                    dist *= nm
                    if acid in acid_conflicts:
                        speed = bs.traf.tas[acidx]
                        
                        # Drone going towards a turn in the first run and away from a turn
                        if (
                            acrte.wpflyturn[current_wp] == True
                            and acrte.wpflyturn[current_wp - 1] == True
                        ):
                            wpqdr, leg_dist = kwikqdrdist(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                            )
                            leg_dist *= nm
                            nextwpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                                acrte.wplat[current_wp + 1],
                                acrte.wplon[current_wp + 1],
                            )

                            prevwpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp - 2],
                                acrte.wplon[current_wp - 2],
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                            )

                            secondturndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )

                            (
                                initialturndist,
                                turnrad,
                                hdgchange,
                            ) = bs.traf.actwp.kwikcalcturn(5 * kts, 25, wpqdr, nextwpqdr)

                            turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)

                            cruise_dist = leg_dist - initialturndist - secondturndist

                            if dist > cruise_dist:
                                # No turn time since turn is made for the second waypoint
                                start_turn = True
                                
                                if speed < 5*kts:
                                    accel_dist = distaccel(speed, 5 * kts, bs.traf.perf.axmax[acidx])
                                    accel_time = (
                                    abs(speed - 5 * kts) / bs.traf.perf.axmax[acidx]
                                    )

                                    # Add it all up
                                    time_diff = (dist - accel_dist) / (5 * kts) + accel_time
                                    time += time_diff
                                    
                                else:
                                    time_diff = dist / (5 * kts)
                                    time += time_diff

                                current_wp += 1
                                first_run = False

                            else:
                                # Add it all up
                                start_turn = True

                                if speed < 5*kts:
                                    accel_dist = distaccel(speed, 5 * kts, bs.traf.perf.axmax[acidx])
                                    accel_time = (
                                    abs(speed - 5 * kts) / bs.traf.perf.axmax[acidx]
                                    )
                                    
                                    if accel_dist > dist- secondturndist:
                                        final_velocity = finalVaccel(dist- secondturndist, speed, bs.traf.perf.axmax[acidx])
                                        accel_time = abs(final_velocity - speed)/ bs.traf.perf.axmax[acidx]
                                        second_run = True
                                        time_diff = accel_time
                                        time += time_diff
                                    else:
                                        # Add it all up
                                        time_diff = (dist - accel_dist- secondturndist) / (5 * kts) + accel_time
                                        time += time_diff
                                    
                                else:
                                    time_diff = (dist - secondturndist) / (5 * kts)
                                    time += time_diff

                                current_wp += 1
                                first_run = False

                                # bs.scr.echo(f"Initial turn Decell region time: {time}")

                        elif acrte.wpflyturn[current_wp] == True:
                            wpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                            )
                            nextwpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                                acrte.wplat[current_wp + 1],
                                acrte.wplon[current_wp + 1],
                            )
                            turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )
                            accel_dist = distaccel(
                                self.cruise_spd, 5 * kts, bs.traf.perf.axmax[acidx]
                            )
                            turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)

                            if dist > turndist + accel_dist:
                                if speed < self.cruise_spd:
                                    accel_conf_dist = distaccel(speed, self.cruise_spd,bs.traf.perf.axmax[acidx])
                                    initial_accel_time = abs(self.cruise_spd - speed)/ bs.traf.perf.axmax[acidx]
                                    cruise_dist = dist - accel_dist - turndist - accel_conf_dist
                                    cruise_time = cruise_dist / (self.cruise_spd)
                                    time_diff = initial_accel_time + cruise_time
                                    time += time_diff
                                    
                                    start_turn = True
                                        
                                else:
                                # Cruise distance
                                    cruise_dist = dist - accel_dist - turndist
                                    cruise_time = cruise_dist / (self.cruise_spd)
                                    time_diff = cruise_time
                                
                                    # Deceleration time
                                    accel_time = (
                                        abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                                    )
    
                                    # No turn time since turn is made for the second waypoint
                                    start_turn = True
    
                                    # Add it all up
                                    time_diff = cruise_time + accel_time
                                    time += time_diff

                                current_wp += 1
                                first_run = False

                                # bs.scr.echo(f"Initial turn Cruise region time: {time}")

                            else:
                                
                                if speed < 5*kts:
                                    accel_dist = distaccel(speed, 5*kts, bs.traf.perf.axmax[acidx])
                                    if dist - turndist < accel_dist:
                                        final_velocity = finalVaccel(dist - turndist,speed, bs.traf.perf.axmax[acidx])
                                        accel_time = (final_velocity - speed)/ bs.traf.perf.axmax[acidx]
                                        time_diff = accel_time
                                        time += time_diff
                                        second_run = True
                                    
                                    else: 
                                        remaining_dist = dist - turndist
                                        accel_time = (speed - 5*kts)/ bs.traf.perf.axmax[acidx]
                                        
                                        cruise_dist = remaining_dist - accel_dist
                                        cruise_time = cruise_dist / (5*kts)
                                        
                                        time_diff = accel_time + cruise_time
                                        time += time_diff
                                        
                                        
                                else:       
                                    # deceleration time
                                    accel_time = (
                                        abs(bs.traf.tas[acidx] - 5 * kts)
                                        / bs.traf.perf.axmax[acidx]
                                    )
                                    # Add it all up
                                    time_diff = accel_time
                                    time += time_diff

                                start_turn = True
                                current_wp += 1
                                first_run = False
                        
                            # Drone going away from a turn in the first run
                        elif acrte.wpflyturn[current_wp - 1] == True:
                            wpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp - 2],
                                acrte.wplon[current_wp - 2],
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                            )
                            nextwpqdr, leg_dist = kwikqdrdist(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                            )
                            leg_dist = leg_dist * nm
                            turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )
                            accel_dist = distaccel(
                                5 * kts, self.cruise_spd, bs.traf.perf.axmax[acidx]
                            )
                            turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)
                            cruise_dist = leg_dist - accel_dist - turndist

                            if dist < accel_dist:
                                if distaccel(speed, self.cruise_spd,bs.traf.perf.axmax[acidx]) > dist:
                                    final_velocity = finalVaccel(dist, speed,bs.traf.perf.axmax[acidx])
                                    accel_time = abs(final_velocity - speed)/ bs.traf.perf.axmax[acidx]
                                    second_run = True
                                    
                                    time_diff = accel_time
                                    time += time_diff
                                
                                else:
                                    # acceleration time
                                    accel_time = (
                                        abs(bs.traf.tas[acidx] - self.cruise_spd)
                                        / bs.traf.perf.axmax[acidx]
                                    )

                                    time_diff = accel_time
                                    time += time_diff

                                current_wp += 1
                                first_run = False

                            elif dist < accel_dist + cruise_dist:
                                if speed < 5*kts:
                                    accel_dist_conf = distaccel(speed, 5*kts, bs.traf.perf.axmax[acidx])
                                    accel_time = (self.cruise_spd - speed)/bs.traf.perf.axmax[acidx]
                                    cruise_time = (dist-accel_dist- accel_dist_conf) / (5*kts)
                                    time_diff = accel_time + cruise_time
                                    time += time_diff
                                
                                else:
                                    # acceleration time
                                    accel_time = (
                                        abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                                    )

                                    # cruise time
                                    partial_cruise_dist = dist - accel_dist
                                    cruise_time = partial_cruise_dist / (5 * kts)

                                    # Add it all up
                                    time_diff = cruise_time + accel_time
                                    time += time_diff

                                current_wp += 1
                                first_run = False

                            else: #WHAT HAPPENS DURING A CONFLICT MID-TURN
                                # acceleration time
                                accel_time = (
                                    abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                                )
                                if speed < 5 *kts:
                                    initial_accel_dist = distaccel(speed, 5*kts, bs.traf.perf.axmax[acidx])
                                    initial_accel_time = abs(5*kts - speed)/ bs.traf.perf.axmax[acidx]
                                    
                                    cruise_dist = cruise_dist - initial_accel_dist
                                    cruise_time = cruise_dist / (5 * kts)
                                    
                                    turn_time = turning_dist * 0.5 / (5 * kts)
                                    
                                    time_diff = cruise_time + accel_time + turn_time + initial_accel_time
                                    time += time_diff
                                    

                                else:
                                    # cruise time
                                    cruise_time = cruise_dist / (5 * kts)

                                    # Turning time
                                    turn_time = turning_dist * 0.5 / (5 * kts)

                                    # Add it all up
                                    time_diff = cruise_time + accel_time + turn_time
                                    time += time_diff

                                current_wp += 1
                                first_run = False

                        # Regular cruise
                        else:
                            if speed < self.cruise_spd:
                                accel_dist = distaccel(speed,self.cruise_spd, bs.traf.perf.axmax[acidx])
                                if accel_dist > dist:
                                    final_velocity = finalVaccel(dist, speed, bs.traf.perf.axmax[acidx])
                                    accel_time = abs(final_velocity - speed)/ bs.traf.perf.axmax[acidx]
                                    time_diff = accel_time
                                    time += time_diff
                                    second_run = True
                                else: 
                                    accel_time = abs(self.cruise_spd - speed)/ bs.traf.perf.axmax[acidx]
                                    cruise_time = (dist-accel_dist)/ (self.cruise_spd)
                                    time_diff = accel_time + cruise_time
                                    time += time_diff
                            else:
                                time += dist / (self.cruise_spd)
                            first_run = False
                            current_wp += 1         

                    # Drone going towards a turn in the first run
                    elif (
                        acrte.wpflyturn[current_wp] == True
                        and acrte.wpflyturn[current_wp - 1] == True
                    ):
                        wpqdr, leg_dist = kwikqdrdist(
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                        )
                        leg_dist *= nm
                        nextwpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                            acrte.wplat[current_wp + 1],
                            acrte.wplon[current_wp + 1],
                        )

                        prevwpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp - 2],
                            acrte.wplon[current_wp - 2],
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                        )

                        secondturndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                            5 * kts, 25, wpqdr, nextwpqdr
                        )

                        (
                            initialturndist,
                            turnrad,
                            hdgchange,
                        ) = bs.traf.actwp.kwikcalcturn(5 * kts, 25, wpqdr, nextwpqdr)

                        turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)

                        cruise_dist = leg_dist - initialturndist - secondturndist

                        if dist > cruise_dist:
                            # No turn time since turn is made for the second waypoint
                            start_turn = True

                            # Add it all up
                            time_diff = dist / (5 * kts)
                            time += time_diff

                            current_wp += 1
                            first_run = False

                        else:
                            # Add it all up
                            start_turn = True

                            time_diff = dist / (5 * kts)
                            time += time_diff

                            current_wp += 1
                            first_run = False

                            # bs.scr.echo(f"Initial turn Decell region time: {time}")

                    elif acrte.wpflyturn[current_wp] == True:
                        wpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                        )
                        nextwpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                            acrte.wplat[current_wp + 1],
                            acrte.wplon[current_wp + 1],
                        )
                        turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                            5 * kts, 25, wpqdr, nextwpqdr
                        )
                        accel_dist = distaccel(
                            self.cruise_spd, 5 * kts, bs.traf.perf.axmax[acidx]
                        )
                        turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)

                        if dist > turndist + accel_dist:
                            # Cruise distance
                            cruise_dist = dist - accel_dist - turndist
                            cruise_time = cruise_dist / (self.cruise_spd)

                            # Deceleration time
                            accel_time = (
                                abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                            )

                            # No turn time since turn is made for the second waypoint
                            start_turn = True

                            # Add it all up
                            time_diff = cruise_time + accel_time
                            time += time_diff

                            current_wp += 1
                            first_run = False

                            # bs.scr.echo(f"Initial turn Cruise region time: {time}")

                        else:
                            # deceleration time
                            accel_time = (
                                abs(bs.traf.tas[acidx] - 5 * kts)
                                / bs.traf.perf.axmax[acidx]
                            )

                            # Turn time half cuz only till current_wp
                            start_turn = True

                            # Add it all up
                            time_diff = accel_time
                            time += time_diff

                            current_wp += 1
                            first_run = False

                            # bs.scr.echo(f"Initial turn Decell region time: {time}")

                    # Drone going away from a turn in the first run
                    elif acrte.wpflyturn[current_wp - 1] == True:
                        wpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp - 2],
                            acrte.wplon[current_wp - 2],
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                        )
                        nextwpqdr, leg_dist = kwikqdrdist(
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                        )
                        leg_dist = leg_dist * nm
                        turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                            5 * kts, 25, wpqdr, nextwpqdr
                        )
                        accel_dist = distaccel(
                            5 * kts, self.cruise_spd, bs.traf.perf.axmax[acidx]
                        )
                        turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)
                        cruise_dist = leg_dist - accel_dist - turndist

                        if dist < accel_dist:
                            # acceleration time
                            accel_time = (
                                abs(bs.traf.tas[acidx] - self.cruise_spd)
                                / bs.traf.perf.axmax[acidx]
                            )

                            time_diff = accel_time
                            time += time_diff

                            current_wp += 1
                            first_run = False

                        elif dist < accel_dist + cruise_dist:
                            # acceleration time
                            accel_time = (
                                abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                            )

                            # cruise time
                            partial_cruise_dist = dist - accel_dist
                            cruise_time = partial_cruise_dist / (5 * kts)

                            # Add it all up
                            time_diff = cruise_time + accel_time
                            time += time_diff

                            current_wp += 1
                            first_run = False

                        else:
                            # acceleration time
                            accel_time = (
                                abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                            )

                            # cruise time
                            cruise_time = cruise_dist / (5 * kts)

                            # Turning time
                            turn_time = turning_dist * 0.5 / (5 * kts)

                            # Add it all up
                            time_diff = cruise_time + accel_time + turn_time
                            time += time_diff

                            current_wp += 1
                            first_run = False

                    # Regular cruise
                    else:
                        time_diff = dist / (self.cruise_spd)
                        time += time_diff
                        first_run = False
                        current_wp += 1
#First run ends here--------------------------------------------------------------------------------------------------------------------------------------------
                elif second_run == True:
                    if start_turn == True:
                        prevwpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp - 2],
                            acrte.wplon[current_wp - 2],
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                        )

                        wpqdr, dist = kwikqdrdist(
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                        )
                        dist = dist * nm

                        turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                            5 * kts, 25, prevwpqdr, wpqdr
                        )
                        initial_turn_time = turning_dist / (5 * kts)
                        initial_turndist = turndist
                        
                        initial_accel_time = abs(final_velocity - 5 *kts)
                        initial_accel_dist = distaccel(final_velocity,5*kts,bs.traf.perf.axmax[acidx])
                        if acrte.wpflyturn[current_wp] == True:
                            nextwpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                            acrte.wplat[current_wp + 1],
                            acrte.wplon[current_wp + 1],
                            )
                            turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )
                            
                            cruise_dist = dist - initial_accel_dist - turndist - initial_turndist
                            cruise_time = cruise_dist / (5*kts)
                            
                            time_diff = initial_turn_time + initial_accel_time + cruise_time
                            time += time_diff
                            second_run = False
                            current_wp +=1
                            
                        else:
                            accel_dist = distaccel(5*kts, self.cruise_spd, bs.traf.perf.axmax[acidx])
                            accel_time = abs(self.cruise_spd - 5*kts)/ bs.traf.perf.axmax[acidx]
                            
                            cruise_dist = dist - accel_dist - initial_accel_dist - initial_turndist
                            cruise_time = cruise_dist/ (5*kts)
                            
                            time_diff = initial_turn_time + initial_accel_time + cruise_time + accel_time
                            time += time_diff
                            
                            second_run = False
                            current_wp +=1
                            start_turn = False
                    
                    else:
                        if acrte.wpflyturn[current_wp] == True:
                            wpqdr, dist = kwikqdrdist(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                            )
                            dist = dist * nm
                            nextwpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                                acrte.wplat[current_wp + 1],
                                acrte.wplon[current_wp + 1],
                            )
                            turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )
                            
                            initial_accel_time = abs(final_velocity - self.cruise_spd)
                            initial_accel_dist = distaccel(final_velocity,self.cruise_spd,bs.traf.perf.axmax[acidx])
                                
                            
                            accel_dist = distaccel(self.cruise_spd, 5*kts, bs.traf.perf.axmax[acidx])
                            accel_time = abs(self.cruise_spd - 5*kts)/ bs.traf.perf.axmax[acidx]
                            
                            #Maybe something for when initial__accel > dist- accel_dist
                            
                            cruise_dist = dist - initial_accel_dist - turndist - accel_dist
                            cruise_time = cruise_dist/ (self.cruise_spd)
                            
                            start_turn = True
                            second_run = False
                            
                            time_diff = initial_accel_time + accel_time + cruise_time
                            time += time_diff
                            current_wp +=1
                            
                        else:
                            _, dist = kwikqdrdist(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                            )
                            dist = dist * nm
                            
                            initial_accel_time = abs(final_velocity - self.cruise_spd)
                            initial_accel_dist = distaccel(final_velocity,self.cruise_spd,bs.traf.perf.axmax[acidx])

                            cruise_dist = dist - initial_accel_dist
                            time_diff = cruise_dist / (self.cruise_spd)
                            time += time_diff
                            
                            second_run = False
                            current_wp += 1
                            
                    
#Second run ends here----------------------------------------------------------------------------------------------------------------------------
                # Iterations after turn
                elif start_turn == True:
                    # second part of initial turn
                    prevwpqdr, _ = kwikqdrdist(
                        acrte.wplat[current_wp - 2],
                        acrte.wplon[current_wp - 2],
                        acrte.wplat[current_wp - 1],
                        acrte.wplon[current_wp - 1],
                    )

                    wpqdr, dist = kwikqdrdist(
                        acrte.wplat[current_wp - 1],
                        acrte.wplon[current_wp - 1],
                        acrte.wplat[current_wp],
                        acrte.wplon[current_wp],
                    )
                    dist = dist * nm

                    turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                        5 * kts, 25, prevwpqdr, wpqdr
                    )
                    turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)

                    if acrte.wpflyturn[current_wp] == True:
                        initial_turn_time = turning_dist / (5 * kts)
                        initial_turndist = turndist

                        # Calculations for the second turn parameters
                        nextwpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                            acrte.wplat[current_wp + 1],
                            acrte.wplon[current_wp + 1],
                        )
                        turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                            5 * kts, 25, wpqdr, nextwpqdr
                        )

                        # Calculate the leg distance, acceleration distance and turning distance (total distance covered by turn) for second turn
                        turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)

                        # Cruise distance with turning speed instead of cruise
                        cruise_dist = dist - turndist - initial_turndist
                        cruise_time = cruise_dist / (5 * kts)

                        # Second turn time times half cuz only till current_wp
                        start_turn = True

                        # Total time
                        time_diff = initial_turn_time + cruise_time
                        time += time_diff

                        current_wp += 1

                    else:
                        # The turn
                        turn_time = turning_dist / (5 * kts)

                        # Acceleration
                        accel_dist = distaccel(
                            5 * kts, self.cruise_spd, bs.traf.perf.axmax[acidx]
                        )
                        accel_time = abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]

                        # Cruise whilst still being in turning speed
                        _, dist = kwikqdrdist(
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                        )
                        dist = dist * nm
                        cruise_dist = dist - accel_dist - turndist
                        cruise_time = cruise_dist / (5 * kts)

                        # Total time
                        time_diff = cruise_time + accel_time + turn_time
                        time += time_diff
                        start_turn = False
                        current_wp += 1

                # Iterations after a regular leg
                else:
                    if acrte.wpflyturn[current_wp] == True:
                        wpqdr, dist = kwikqdrdist(
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                        )
                        dist = dist * nm
                        nextwpqdr, _ = kwikqdrdist(
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                            acrte.wplat[current_wp + 1],
                            acrte.wplon[current_wp + 1],
                        )
                        turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                            5 * kts, 25, wpqdr, nextwpqdr
                        )

                        # Calculate the leg distance, acceleration distance and turning distance (total distance covered by turn)
                        accel_dist = distaccel(
                            self.cruise_spd, 5 * kts, bs.traf.perf.axmax[acidx]
                        )
                        turning_dist = abs(2 * np.pi * turnrad * hdgchange / 360)

                        # Cruise distance
                        cruise_dist = dist - accel_dist - turndist
                        cruise_time = cruise_dist / (self.cruise_spd)

                        # Deceleration time
                        accel_time = abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]

                        # Turn  time times half cuz only till current_wp
                        start_turn = True

                        # Add it all up
                        time_diff = cruise_time + accel_time
                        time += time_diff

                        current_wp += 1

                    else:
                        _, dist = kwikqdrdist(
                            acrte.wplat[current_wp - 1],
                            acrte.wplon[current_wp - 1],
                            acrte.wplat[current_wp],
                            acrte.wplon[current_wp],
                        )
                        dist = dist * nm
                        time_diff = dist / (self.cruise_spd)
                        time += time_diff
                        current_wp += 1


                #print(f"current wp {current_wp -1}")
                # --------------------------------------------------------------------------------------------------------------------------------------------------
                # Position Calculations
                if floor_div < time // measurement_freq:
                    i = 0
                    value = int(time // measurement_freq) - floor_div
                    while i < value and floor_div < self.dtlookahead_def / measurement_freq:
                        floor_div += 1
                        overshoot_time = time - floor_div * measurement_freq

                        if (
                            acrte.wpflyturn[current_wp - 1] == True
                            and acrte.wpflyturn[current_wp - 2] == True
                        ):
                            wpqdr, dist = kwikqdrdist(
                                acrte.wplat[current_wp - 2],
                                acrte.wplon[current_wp - 2],
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                            )
                            dist = dist * nm
                            nextwpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                            )

                            prevwpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp - 3],
                                acrte.wplon[current_wp - 3],
                                acrte.wplat[current_wp - 2],
                                acrte.wplon[current_wp - 2],
                            )
                            (
                                initial_turndist,
                                initial_turnrad,
                                initial_hdgchange,
                            ) = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, prevwpqdr, wpqdr
                            )
                            (
                                second_turndist,
                                turnrad,
                                hdgchange,
                            ) = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )

                            initial_turning_dist = abs(
                                2 * np.pi * initial_turnrad * initial_hdgchange / 360
                            )

                            initial_turn_time = initial_turning_dist / (5 * kts)

                            cruise_dist = dist - initial_turndist - second_turndist
                            cruise_time = cruise_dist / (5 * kts)

                            # Ends in cruise
                            if overshoot_time < cruise_time:
                                overshoot_dist = overshoot_time * 5 * kts

                                bearing, _ = kwikqdrdist(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    acrte.wplat[current_wp - 2],
                                    acrte.wplon[current_wp - 2],
                                )
                                final_lat, final_lon = kwikpos(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    bearing,
                                    overshoot_dist / nm,
                                )

                            # Ends in cruise part before turn
                            else:
                                final_lat = acrte.wplat[current_wp - 2]
                                final_lon = acrte.wplon[current_wp - 2]

                        elif acrte.wpflyturn[current_wp - 1] == True:
                            wpqdr, dist = kwikqdrdist(
                                acrte.wplat[current_wp - 2],
                                acrte.wplon[current_wp - 2],
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                            )
                            dist = dist * nm
                            nextwpqdr, _ = kwikqdrdist(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                acrte.wplat[current_wp],
                                acrte.wplon[current_wp],
                            )
                            turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )

                            accel_dist = distaccel(
                                self.cruise_spd, 5 * kts, bs.traf.perf.axmax[acidx]
                            )
                            accel_time = (
                                abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                            )

                            # Ends in deceleration part before turn
                            if overshoot_time < accel_time:
                                overshoot_dist = (
                                    0.5
                                    * bs.traf.perf.axmax[acidx]
                                    * (overshoot_time) ** 2
                                    + 5 * kts * overshoot_time
                                )
                                bearing, _ = kwikqdrdist(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    acrte.wplat[current_wp - 2],
                                    acrte.wplon[current_wp - 2],
                                )
                                final_lat, final_lon = kwikpos(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    bearing,
                                    overshoot_dist / nm,
                                )

                            # Ends in cruise part before turn
                            else:
                                remaining_time = overshoot_time - accel_time
                                overshoot_dist = accel_dist + remaining_time * self.cruise_spd
                                bearing, _ = kwikqdrdist(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    acrte.wplat[current_wp - 2],
                                    acrte.wplon[current_wp - 2],
                                )
                                final_lat, final_lon = kwikpos(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    bearing,
                                    overshoot_dist / nm,
                                )

                        elif acrte.wpflyturn[current_wp - 2] == True:
                            wpqdr, dist = kwikqdrdist(
                                acrte.wplat[current_wp - 3],
                                acrte.wplon[current_wp - 3],
                                acrte.wplat[current_wp - 2],
                                acrte.wplon[current_wp - 2],
                            )
                            dist = dist * nm
                            nextwpqdr, leg_dist = kwikqdrdist(
                                acrte.wplat[current_wp - 2],
                                acrte.wplon[current_wp - 2],
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                            )
                            leg_dist *= nm
                            turndist, turnrad, hdgchange = bs.traf.actwp.kwikcalcturn(
                                5 * kts, 25, wpqdr, nextwpqdr
                            )

                            accel_dist = distaccel(
                                self.cruise_spd, 5 * kts, bs.traf.perf.axmax[acidx]
                            )
                            accel_time = (
                                abs(self.cruise_spd - 5 * kts) / bs.traf.perf.axmax[acidx]
                            )

                            cruise_dist = leg_dist - turndist - accel_dist
                            cruise_time = cruise_dist / (5 * kts)
                            
                            if overshoot_time < accel_time:
                                overshoot_dist = (
                                    -0.5
                                    * bs.traf.perf.axmax[acidx]
                                    * (overshoot_time) ** 2
                                    + self.cruise_spd * overshoot_time
                                )
                                bearing, _ = kwikqdrdist(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    acrte.wplat[current_wp - 2],
                                    acrte.wplon[current_wp - 2],
                                )
                                final_lat, final_lon = kwikpos(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    bearing,
                                    overshoot_dist / nm,
                                )

                            elif overshoot_time < accel_time + cruise_time:
                                remaining_time = overshoot_time - accel_time
                                overshoot_dist = accel_dist + remaining_time * 5 * kts
                                bearing, _ = kwikqdrdist(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    acrte.wplat[current_wp - 2],
                                    acrte.wplon[current_wp - 2],
                                )
                                final_lat, final_lon = kwikpos(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    bearing,
                                    overshoot_dist / nm,
                                )

                            else:
                                final_lat = acrte.wplat[current_wp - 2]
                                final_lon = acrte.wplon[current_wp - 2]

                        else:
                            overshoot_dist = overshoot_time * self.cruise_spd
                            if (
                                acrte.wplat[current_wp - 1]
                                == acrte.wplat[current_wp - 2]
                            ):
                                bearing, _ = kwikqdrdist(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    bs.traf.lat[acidx],
                                    bs.traf.lon[acidx],
                                )
                            else:
                                bearing, _ = kwikqdrdist(
                                    acrte.wplat[current_wp - 1],
                                    acrte.wplon[current_wp - 1],
                                    acrte.wplat[current_wp - 2],
                                    acrte.wplon[current_wp - 2],
                                )
                            final_lat, final_lon = kwikpos(
                                acrte.wplat[current_wp - 1],
                                acrte.wplon[current_wp - 1],
                                bearing,
                                overshoot_dist / nm,
                            )

                        # Data record
                        array_measurement.append(
                            [acid, floor_div, final_lat, final_lon, current_wp -1]
                        )
                        i += 1
                try:
                    acrte.wpflyturn[current_wp]
                except:
                    break

        #print("---------------------------------------------------------------------------------")
        confpairs = []
        confinfo = []
        df = pd.DataFrame(array_measurement, columns=["acid", "part", "lat", "lon", "waypoint"])

        #if self.plot_toggle:
        #    for i in range(len(df)):
        #        plt.scatter(
        #            df.iloc[i].lon,
        #            df.iloc[i].lat,
        #            color="blue",
        #            label=f"{df.acid}",
        #        )
        #        plt.text(df.iloc[i].lon, df.iloc[i].lat, str(i))
        #    plt.show()

        try:
            parts = max(df["part"])
        except:
            #print("No more tings")
            pass
        else:
            parts = max(df["part"])

            for i in range(1, parts + 1):
                qdr, dist = geo.kwikqdrdist_matrix(
                    np.asmatrix(df[df["part"] == i].lat),
                    np.asmatrix(df[df["part"] == i].lon),
                    np.asmatrix(df[df["part"] == i].lat),
                    np.asmatrix(df[df["part"] == i].lon),
                )
                I = np.eye(len(df[df["part"] == i]["acid"].unique()))
                qdr = np.asarray(qdr)
                qdr = qdr
                dist = np.asarray(dist) * nm + 1e9 * I
                conflicts = np.column_stack(np.where(dist < rpz))
                for pair in conflicts:
                    #print(pair)
                    #print(df[df["part"] == i].acid.unique())
                    #print(len(df[df["part"] == i].acid.unique()))
                    #print("------------------------------------------------------------------------------------------")
                    conflictpair = (df[df["part"] == i].acid.unique()[pair[0]], df[df["part"] == i].acid.unique()[pair[1]])
                    if conflictpair not in confpairs:
                        #bs.scr.echo(f"{conflictpair}")
                        coords1 = []
                        coords2 = []
                        acrte1 = Route._routes.get(conflictpair[0])
                        acrte2 = Route._routes.get(conflictpair[1])
                        waypoint1 = int(df[(df["acid"] == conflictpair[0]) & (df["part"] == i)].waypoint)
                        waypoint2 = int(df[(df["acid"] == conflictpair[1]) & (df["part"] == i)].waypoint)
                        
                        conf_dist = 0
                        j = acrte1.iactwp
                        currentwp = acrte1.wplat[j], acrte1.wplon[j]
                        while conf_dist < 300:
                            if j == len(acrte1.wplat)-2:
                                coords1.append((acrte1.wplon[j], acrte1.wplat[j]))
                                break
                            # Now, get next wp
                            try:
                                acrte1.wplat[j+1]
                            except: 
                                coords1.append((acrte1.wplon[j], acrte1.wplat[j]))
                                break
                            nextwp = (acrte1.wplat[j+1], acrte1.wplon[j+1])
                            # Get the distance
                            conf_dist += kwikdist(currentwp[0], currentwp[1], nextwp[0], nextwp[1]) * nm
                            # Add wp
                            coords1.append((nextwp[1], nextwp[0]))
                            # Set new wp
                            j += 1
                            currentwp = nextwp
                        
                        conf_dist = 0    
                        j = acrte2.iactwp
                        currentwp = acrte2.wplat[j], acrte2.wplon[j]
                        while conf_dist < 300:
                            if j == len(acrte2.wplat)-2:
                                coords2.append((acrte2.wplon[j], acrte2.wplat[j]))
                                break
                            # Now, get next wp
                            try:
                                acrte2.wplat[j+1]
                            except: 
                                coords2.append((acrte2.wplon[j], acrte2.wplat[j]))
                                break
                            nextwp = (acrte2.wplat[j+1], acrte2.wplon[j+1])
                            # Get the distance
                            conf_dist += kwikdist(currentwp[0], currentwp[1], nextwp[0], nextwp[1]) * nm
                            # Add wp
                            coords2.append((nextwp[1], nextwp[0]))
                            # Set new wp
                            j += 1
                            currentwp = nextwp

                        #for j in range(10):
                        #    try:
                        #        acrte1.wplat[waypoint1 +j]
                        #    except:
                        #        pass
                        #    else:
                        #        coords1.append((acrte1.wplat[waypoint1 +j], acrte1.wplon[waypoint1 +j]))
                        #        
                        #    try:
                        #        acrte2.wplat[waypoint2 +j]
                        #    except:
                        #        pass
                        #    else:
                        #        coords2.append((acrte2.wplat[waypoint2 +j], acrte2.wplon[waypoint2 +j]))
                        
                        if len(coords1) >1:
                            linestring1 = sh.LineString(coords1)
                        
                        else:
                            linestring1 = sh.Point(coords1)
                            
                        if len(coords2) >1:
                            linestring2 = sh.LineString(coords2)
                        else:
                            linestring2 = sh.Point(coords2)

                        #bs.scr.echo(f"distance {linestring1.intersects(linestring2)}")
                        #print(linestring1.intersects(linestring2))
                        if linestring1.intersects(linestring2):
                            confpairs.append(conflictpair)
                            confinfo.append([conflictpair, i, waypoint1, waypoint2])

        # Conflict Pairs
        #if confpairs:
        #    bs.scr.echo(f"{confpairs}")
        self.confpairs = confpairs

        # Conflict plot
        if self.plot_toggle:
            done_pairs = []
            for entry in confpairs:
                if entry[0] and entry[1] in done_pairs:
                    continue
                done_pairs.append(entry[0])
                
                done_pairs.append(entry[1])
                timer = 0
                fig = plt.figure()
                ax = fig.add_subplot()
                plt.scatter(
                    df[df["acid"] == entry[0]].lon,
                    df[df["acid"] == entry[0]].lat,
                    color="blue",
                    label=f"{entry[0]}",
                )
                plt.scatter(
                    df[df["acid"] == entry[1]].lon,
                    df[df["acid"] == entry[1]].lat,
                    color="red",
                    label=f"{entry[1]}",
                )
                for coords in zip(
                    df[df["acid"] == entry[0]].lon,
                    df[df["acid"] == entry[0]].lat,
                    df[df["acid"] == entry[1]].lon,
                    df[df["acid"] == entry[1]].lat
                ):
                    ax.add_patch(
                        Circle(
                            coords[:2], radius=0.0005, ec="blue", fc="none", alpha=0.6
                        )
                    )
                    ax.add_patch(
                        Circle(
                            coords[2:4], radius=0.0005, ec="red", fc="none", alpha=0.6
                        )
                    )
                    plt.text(coords[0], coords[1], str(timer))
                    plt.text(coords[2], coords[3], str(timer))
                    timer += 1

                ax.set_aspect("equal", adjustable="box")
                ax.legend()
            plt.show()

        confpairs_idx = [
            (bs.traf.id2idx(acid1), bs.traf.id2idx(acid2)) for acid1, acid2 in confpairs
        ]

        inconf = np.zeros(bs.traf.ntraf)
        for idx1, idx2 in confpairs_idx:
            inconf[idx1] = 1

        self.inconf = inconf

        # LoS Pairs
        I = np.eye(ownship.ntraf)
        _, dist_state = qdr, dist = geo.kwikqdrdist_matrix(
            np.asmatrix(ownship.lat),
            np.asmatrix(ownship.lon),
            np.asmatrix(intruder.lat),
            np.asmatrix(intruder.lon),
        )
        dist_state = np.asarray(dist_state) * nm + 1e9 * I
        swlos = dist_state < rpz
        lospairs = [(ownship.id[i], ownship.id[j]) for i, j in zip(*np.where(swlos))]
        # bs.scr.echo(f"{lospairs}")
        self.lospairs = lospairs
        bs.scr.echo(f"{confpairs}")

        return confpairs, inconf, lospairs, df, confinfo

    def sb_detect(self, ownship, intruder, rpz, hpz, dtlookahead):
        """State-based detection."""
        # Identity matrix of order ntraf: avoid ownship-ownship detected conflicts
        I = np.eye(ownship.ntraf)

        # Horizontal conflict ------------------------------------------------------

        # qdrlst is for [i,j] qdr from i to j, from perception of ADSB and own coordinates
        qdr, dist = geo.kwikqdrdist_matrix(
            np.asmatrix(ownship.lat),
            np.asmatrix(ownship.lon),
            np.asmatrix(intruder.lat),
            np.asmatrix(intruder.lon),
        )

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
        dxinhor = np.sqrt(
            np.maximum(0.0, R2 - dcpa2)
        )  # half the distance travelled inzide zone
        dtinhor = dxinhor / vrel

        tinhor = np.where(swhorconf, tcpa - dtinhor, 1e8)  # Set very large if no conf
        touthor = np.where(swhorconf, tcpa + dtinhor, -1e8)  # set very large if no conf

        # Vertical conflict --------------------------------------------------------

        # Vertical crossing of disk (-dh,+dh)
        dalt = (
            ownship.alt.reshape((1, ownship.ntraf))
            - intruder.alt.reshape((1, ownship.ntraf)).T
            + 1e9 * I
        )

        dvs = (
            ownship.vs.reshape(1, ownship.ntraf)
            - intruder.vs.reshape(1, ownship.ntraf).T
        )
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

        swconfl = np.array(
            swhorconf
            * (tinconf <= toutconf)
            * (toutconf > 0.0)
            * np.asarray(tinconf < np.asmatrix(dtlookahead).T)
            * (1.0 - I),
            dtype=bool,
        )

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

        return (
            confpairs,
            lospairs,
            inconf,
            tcpamax,
            qdr[swconfl],
            dist[swconfl],
            np.sqrt(dcpa2[swconfl]),
            tcpa[swconfl],
            tinconf[swconfl],
            qdr,
            dist,
        )
        
    @command
    def setlookahead(self,lookaheadtime):
        self.dtlookahead_def = int(lookaheadtime)
        return

    def update_log(self):
        """Here, we are logging the information for current conflicts as well as
        whether these conflicts resulted in a LOS or not."""
        confpairs_new = list(set(self.confpairs) - self.prevconfpairs)  # New confpairs
        confpairs_out = list(
            self.prevconfpairs - set(self.confpairs)
        )  # Pairs that are no longer in conflict
        lospairs_new = list(set(self.lospairs) - self.prevlospairs)  # New lospairs

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
                    bs.traf.alt[idx2],
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
                # print(dictkey)
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
                    # print('huh')
                    continue

                self.uniqueconfloslog.log(
                    self.unique_conf_dict[dictkey][0],
                    str(self.unique_conf_dict[dictkey][1]),
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
                str(self.unique_conf_dict[dictkey][1]),
            )
            self.unique_conf_dict.pop(dictkey)

        self.prevconfpairs = set(self.confpairs)
        self.prevlospairs = set(self.lospairs)

    @command
    def toggle_plot(self):
        if self.plot_toggle:
            self.plot_toggle = False
            bs.scr.echo(f"plots are off")
        else:
            self.plot_toggle = True
            bs.scr.echo(f"plots are on")


def distaccel(v0, v1, axabs):
    """Calculate distance travelled during acceleration/deceleration
    v0 = start speed, v1 = endspeed, axabs = magnitude of accel/decel
    accel/decel is detemremind by sign of v1-v0
    axabs is acceleration/deceleration of which absolute value will be used
    solve for x: x = vo*t + 1/2*a*t*t    v = v0 + a*t"""
    return 0.5 * np.abs(v1 * v1 - v0 * v0) / np.maximum(0.001, np.abs(axabs))

def finalVaccel(dist, v0, axabs):
    return np.sqrt(2*axabs*dist + v0**2)

def clip_route(idx, dist_front, dist_back):
        route = bs.traf.ap.route[idx]
        i = route.iactwp
        currentwp = (bs.traf.lat[idx], bs.traf.lon[idx])
        front_wp_list = []
        back_wp_list = []
        dist = 0
        while dist < dist_back:
            if i == 0:
                break
            # Now, get previous wp
            prevwp = (route.wplat[i-1], route.wplon[i-1])
            # Get the distance
            dist += kwikdist(currentwp[0], currentwp[1], prevwp[0], prevwp[1]) * nm
            # Add wp
            back_wp_list.append((prevwp[0], prevwp[1]))
            # Set new wp
            i -= 1
            currentwp = prevwp
        # Reverse
        back_wp_list.reverse()
        # front
        i = route.iactwp
        dist = 0
        currentwp = (bs.traf.lat[idx], bs.traf.lon[idx])
        while dist < dist_front:
            if i >= len(route.wplat)-2:
                break
            # Now, get next wp
            nextwp = (route.wplat[i+1], route.wplon[i+1])
            # Get the distance
            dist += kwikdist(currentwp[0], currentwp[1], nextwp[0], nextwp[1]) * nm
            # Add wp
            front_wp_list.append((nextwp[0], nextwp[1]))
            # Set new wp
            i += 1
            currentwp = nextwp
            
        # Put the list together
        return back_wp_list, front_wp_list
