import numpy as np
import bluesky as bs
import copy
import pandas as pd
from bluesky.traffic.asas import ConflictResolution
from bluesky.core import Entity
from bluesky.tools.aero import kts
from bluesky.tools.geo import kwikqdrdist, kwikpos, kwikdist
from bluesky.traffic import Route
from shapely.geometry import Point
from collections import Counter


def init_plugin():
    # Addtional initilisation code

    # Configuration parameters
    config = {
        # The name of your plugin
        "plugin_name": "JasonCR",
        # The type of this plugin. For now, only simulation plugins are possible.
        "plugin_type": "sim",
    }

    return config


class JasonCR(ConflictResolution):
    def __init__(self):
        super().__init__()
        self.apdict = dict()
        
      # Some helper functions
    def norm_sq(self, x):
        return np.dot(x, x)
   
    def norm(self,x):
        return np.sqrt(self.norm_sq(x))

    def resolve(self, conf, ownship, intruder):
        # Get all the values from CD that we would need
        confpairs = conf.confpairs  # Pair IDs in conflict
        df = conf.df
        confinfo = conf.confinfo
        dupes = []
        used_dr = []
        conflist= []
        for x,y in confpairs:
            conflist.append(x)
            
        confcounter = Counter(conflist) 

        # Copies of aircraft autopilot stuff
        newgs = np.copy(ownship.ap.tas)
        newvs = np.copy(ownship.ap.vs)
        newalt = np.copy(ownship.ap.alt)
        newtrack = np.copy(ownship.ap.trk)

        for entry in confinfo:
            self.apdict[entry[0][0]] = True
            # Get the aircraft IDX
            flag = False
            coords_list = []
            ownship_idx = bs.traf.id2idx(entry[0][0])
            intruder_idx = bs.traf.id2idx(entry[0][1])
            
            acrte1 = Route._routes.get(entry[0][0])
            acrte2 = Route._routes.get(entry[0][1])
            
            for i in range(10):
                try:
                    acrte1.wplat[entry[2] + i]
                except:
                    break
                else:
                    coords_list.append((acrte1.wplat[entry[2] + i], acrte1.wplon[entry[2] + i]))
                
            for i in range(10):
                try:
                    acrte2.wplat[entry[3] + i]
                except:
                    break
                else:
                    if (acrte2.wplat[entry[3] + i], acrte2.wplon[entry[3] + i]) in coords_list:
                        dist1 = kwikdist(bs.traf.lat[ownship_idx], bs.traf.lon[ownship_idx], acrte2.wplat[entry[3] + i], acrte2.wplon[entry[3] + i])
                        dist2 = kwikdist(bs.traf.lat[intruder_idx], bs.traf.lon[intruder_idx], acrte2.wplat[entry[3] + i], acrte2.wplon[entry[3] + i])
                        if dist1 >= dist2:
                            newgs[ownship_idx] = 0
                            self.apdict[entry[0][0]] = False
                            #bs.scr.echo(f"slowing down {entry[0][0]}")
                        flag = True
                        break
            
            
            if flag:
                continue
            
            #bs.scr.echo(f"{entry[0][0]} waypoint {entry[2]} | {entry[0][1]} waypoint {entry[3]}")
                
            if confcounter[entry[0][0]] > 1 and confcounter[entry[0][0]] >= confcounter[entry[0][1]]:
                newgs[ownship_idx] = 0
                self.apdict[entry[0][0]] = False
                #bs.scr.echo("it happened 2")
                if confcounter[entry[0][0]] >= confcounter[entry[0][1]]:
                    confcounter[entry[0][0]] += 1
                
            #elif confcounter[entry[0][1]] > 1 and confcounter[entry[0][0]] < confcounter[entry[0][1]]:
            #    newgs[intruder_idx] = 0
            #    bs.scr.echo("it happened 3")
            
            
            else:
                #bs.scr.echo("It happened 4")
                if ownship_idx > intruder_idx:
                    newgs[ownship_idx] = 0
                    self.apdict[entry[0][0]] = False

        return newtrack, newgs, newvs, newalt

    def JasonResolve(
        self, conf, ownship_idx, intruder_idx, predicted_waypoints, qdr_mat, dist_mat
    ):
        # Just make it stop (horrible idea if left like this, all aircraft will stop
        return 0

    # We want to override the HDGACTIVE flag for aircraft to always follow the heading from AP
    @property
    def hdgactive(self):
        """Return a boolean array sized according to the number of aircraft
        with True for all elements where heading is currently controlled by
        the conflict resolution algorithm.
        """
        return np.array([False] * len(self.active))

    @property
    def vsactive(self):
        """Return a boolean array sized according to the number of aircraft
        with True for all elements where heading is currently controlled by
        the conflict resolution algorithm.
        """
        return np.array([False] * len(self.active))

    @property
    def altactive(self):
        """Return a boolean array sized according to the number of aircraft
        with True for all elements where heading is currently controlled by
        the conflict resolution algorithm.
        """
        return np.array([False] * len(self.active))

    #Need to overwrite resumenav
    def resumenav(self, conf, ownship, intruder):
        """
        Decide for each aircraft in the conflict list whether the ASAS
        should be followed or not, based on if the aircraft pairs passed
        their CPA.
        """
        # Add new conflicts to resopairs and confpairs_all and new losses to lospairs_all
        self.resopairs.update(conf.confpairs) 
        # Conflict pairs to be deleted
        delpairs = set()
        changeactive = dict()   
        # smallest relative angle between vectors of heading a and b
        def anglediff(a, b):
            d = a - b
            if d > 180:
                return anglediff(a, b + 360)
            elif d < -180:
                return anglediff(a + 360, b)
            else:
                return d    
        # Look at all conflicts, also the ones that are solved but CPA is yet to come
        for conflict in self.resopairs:
            idx1, idx2 = bs.traf.id2idx(conflict)
            # If the ownship aircraft is deleted remove its conflict from the list
            if idx1 < 0:
                delpairs.add(conflict)
                #self.stopping_dict.pop(bs.traf.id[idx1] + bs.traf.id[idx2], False)
                continue
            
            if idx2 >= 0:
                # Distance vector using flat earth approximation
                re = 6371000.0
                dist = re * np.array(
                    [
                        np.radians(intruder.lon[idx2] - ownship.lon[idx1])
                        * np.cos(
                            0.5 * np.radians(intruder.lat[idx2] + ownship.lat[idx1])
                        ),
                        np.radians(intruder.lat[idx2] - ownship.lat[idx1]),
                    ]
                )   
                # Relative velocity vector
                vrel = np.array(
                    [
                        intruder.gseast[idx2] - ownship.gseast[idx1],
                        intruder.gsnorth[idx2] - ownship.gsnorth[idx1],
                    ]
                )   
                # Check if conflict is past CPA
                past_cpa = np.dot(dist, vrel) > 0.0 
                ###### ANDREI'S CHANGE ###############
                # Also check the distance between aircraft
                distance = self.norm(dist)
                # We want enough distance between aircraft
                dist_ok = distance > 2 * bs.traf.cd.rpz_def
                ######################################  
                rpz = np.max(conf.rpz[[idx1, idx2]])
                # hor_los:
                # Aircraft should continue to resolve until there is no horizontal
                # LOS. This is particularly relevant when vertical resolutions
                # are used.
                hdist = np.linalg.norm(dist)
                hor_los = hdist < rpz   
                # Bouncing conflicts:
                # If two aircraft are getting in and out of conflict continously,
                # then they it is a bouncing conflict. ASAS should stay active until
                # the bouncing stops.
                is_bouncing = (
                    abs(anglediff(ownship.trk[idx1], intruder.trk[idx2])) < 30.0
                    and hdist < rpz * self.resofach
                )   
            # Start recovery for ownship if intruder is deleted, or if past CPA
            # and not in horizontal LOS or a bouncing conflict
            if idx2 >= 0 and (not past_cpa or hor_los or is_bouncing or not dist_ok):
                ##### ANDREI'S CHANGE -> also added the dist_ok here ----  ^
                # Enable ASAS for this aircraft
                changeactive[idx1] = True
                # Ok but check if we can set AP speed for the ownship
                #if conflict[0] in self.apdict and self.apdict[conflict[0]]:
                #    bs.traf.cr.tas[idx1] = bs.traf.ap.tas[idx1]
                    
            else:
                # Switch ASAS off for ownship if there are no other conflicts
                # that this aircraft is involved in.
                changeactive[idx1] = changeactive.get(idx1, False)
                # If conflict is solved, remove it from the resopairs list
                delpairs.add(conflict)
                # Remove this pair from the ap dict
                #self.apdict.pop(conflict[0])
        for idx, active in changeactive.items():
            # Loop a second time: this is to avoid that ASAS resolution is
            # turned off for an aircraft that is involved simultaneously in
            # multiple conflicts, where the first, but not all conflicts are
            # resolved.
            self.active[idx] = active
            if not active:
                # Waypoint recovery after conflict: Find the next active waypoint
                # and send the aircraft to that waypoint.
                iwpid = bs.traf.ap.route[idx].findact(idx)
                if iwpid != -1:  # To avoid problems if there are no waypoints
                    bs.traf.ap.route[idx].direct(
                        idx, bs.traf.ap.route[idx].wpname[iwpid]
                    )   
        # Remove pairs from the list that are past CPA or have deleted aircraft
        self.resopairs -= delpairs      