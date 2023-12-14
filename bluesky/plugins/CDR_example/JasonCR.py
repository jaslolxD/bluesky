import numpy as np
import bluesky as bs
import copy
import pandas as pd
from bluesky.traffic.asas import ConflictResolution
from bluesky.core import Entity
from bluesky.tools.aero import kts, ft, nm
from bluesky.tools.geo import kwikqdrdist, kwikpos, kwikdist
from bluesky.traffic import Route
import shapely as sh
from collections import Counter
from shapely.ops import nearest_points


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
        
        # Get initial list of speeds
        speed_to_set = [[x] for x in bs.traf.gs]
        
        # Get qdr
        qdr, _ = bs.tools.geo.kwikqdrdist_matrix(
            np.asmatrix(ownship.lat),
            np.asmatrix(ownship.lon),
            np.asmatrix(intruder.lat),
            np.asmatrix(intruder.lon),
        )

        for entry in confinfo:
            # Check if any of em deleted
            #self.apdict[entry[0][0]] = True
            # Get the aircraft IDX
            ownship_idx = bs.traf.id2idx(entry[0][0])
            intruder_idx = bs.traf.id2idx(entry[0][1])
            
            #acrte1 = Route._routes.get(entry[0][0])
            #acrte2 = Route._routes.get(entry[0][1])
            idx_pair = confpairs.index((entry[0][0], entry[0][1]))
            qdr_pair = qdr[ownship_idx, intruder_idx]
            qdr_intruder = ((qdr_pair - ownship.trk[ownship_idx]) + 180) % 360 - 180  
            qdr_difference = ((qdr_pair - ownship.trk[intruder_idx]) + 180) % 360 - 180
            intr_in_front = (-20 < qdr_intruder < 20)
            intr_in_back = (qdr_intruder < -160 or 160 < qdr_intruder)
            intr_front_aligned = intr_in_front and -20< qdr_difference < 20
            
            # Get the back and front routes of this ownship
            back_list, front_list = self.clip_route(ownship_idx, 300, 300)
            
            if len(back_list) > 1:
                back_string = sh.LineString(back_list)
            else: 
                back_string = sh.Point(back_list)
                
            if len(front_list) >1:
                front_string = sh.LineString(front_list)
            else:
                front_string = sh.Point(front_list)
                
            front_nearest = nearest_points(front_string, sh.Point(bs.traf.lat[intruder_idx], bs.traf.lon[intruder_idx]))[0]
            front_dist = kwikdist(front_nearest.x,front_nearest.y,bs.traf.lat[intruder_idx], bs.traf.lon[intruder_idx]) * nm
            
            back_nearest = nearest_points(back_string, sh.Point(bs.traf.lat[intruder_idx], bs.traf.lon[intruder_idx]))[0]
            back_dist = kwikdist(back_nearest.x,back_nearest.y,bs.traf.lat[intruder_idx], bs.traf.lon[intruder_idx]) * nm
            
            # Check if loss of separation
            #los = kwikdist(bs.traf.lat[ownship_idx], bs.traf.lon[ownship_idx], bs.traf.lat[intruder_idx], bs.traf.lon[intruder_idx]) * nm < bs.traf.cd.rpz_def
            
            if (front_dist < 1 and front_dist < back_dist) or intr_front_aligned:
                speed_to_set[ownship_idx].append(bs.traf.gs[intruder_idx])
                continue
                
            elif back_dist < 1 or intr_in_back:
                # We're in the front, continue
                continue
            
            # Get the problem waypoints
            conf_wp_own_idx, conf_wp_intr_idx = entry[2], entry[3]
            
            # Calculate the distance to the problem waypoints
            dist_ownship = self.calc_dist_to_wp_idx(ownship_idx, conf_wp_own_idx)
            dist_intruder = self.calc_dist_to_wp_idx(intruder_idx, conf_wp_intr_idx)
            
            if dist_ownship < dist_intruder:
                # We have priority
                continue
            elif dist_ownship > dist_intruder:
                # They have priority, stop, but only 60m from problem wp
                speed_to_set[ownship_idx].append(0)
            else:
                # Perfectly equal distance, use ACID
                if ownship_idx > intruder_idx:
                    bs.scr.echo(f"It happened 4 for {entry[0][0]}")
                    speed_to_set[ownship_idx].append(0)
        
        # Get the smallest commanded speed for each aircraft in conflict
        newgs = np.array([min(x) for x in speed_to_set])
        return newtrack, newgs, newvs, newalt
    
    def calc_dist_to_wp_idx(self, acidx, wpidx):
        # Calculates the distance from the current aircraft position to the specified wpidx in the future route.
        # Get the route
        acrte = bs.traf.ap.route[acidx]
        iactwp = acrte.iactwp
        # Sanity check
        if iactwp > wpidx:
            return 0
        # First add the distance from current ac position to current wp
        dist = kwikdist(bs.traf.lat[acidx], bs.traf.lon[acidx], acrte.wplat[iactwp], acrte.wplon[iactwp]) * nm
        # Then, let's check the other waypoints
        if iactwp == wpidx:
            return dist
        
        i = iactwp
        while i < wpidx:
            dist += kwikdist(acrte.wplat[i], acrte.wplon[i], acrte.wplat[i+1], acrte.wplon[i+1]) * nm
            i += 1
        return dist

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
        qdr, _ = bs.tools.geo.kwikqdrdist_matrix(
                    np.asmatrix(ownship.lat),
                    np.asmatrix(ownship.lon),
                    np.asmatrix(intruder.lat),
                    np.asmatrix(intruder.lon),
                )
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
                # If AP speed is lower than the CR speed, update it, as we're probably turning.
                if self.tas[idx1] > bs.traf.ap.tas[idx1]:
                    self.tas[idx1] = bs.traf.ap.tas[idx1]
                    
                # However, if we have priority, we can resume normal operations
                qdr_pair = qdr[idx1, idx2]
                qdr_intruder = ((qdr_pair - ownship.trk[idx1]) + 180) % 360 - 180  
                intr_in_back = (qdr_intruder < -160 or 160 < qdr_intruder)
                if intr_in_back or (idx1 > idx2 and bs.traf.gs[idx1] < 1 and bs.traf.gs[idx2] < 1):
                    # Set the speed to the autopilot one
                    self.tas[idx1] = bs.traf.ap.tas[idx1]
                    
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
        
    def clip_route(self, idx, dist_front, dist_back):
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