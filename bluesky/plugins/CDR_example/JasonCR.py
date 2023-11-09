import numpy as np
import bluesky as bs
import copy
from bluesky.traffic.asas import ConflictResolution
from bluesky.core import Entity
from bluesky.tools.aero import kts
from shapely.geometry import Point


def init_plugin():

    # Addtional initilisation code

    # Configuration parameters
    config = {
        # The name of your plugin
        'plugin_name':     'JasonCR',

        # The type of this plugin. For now, only simulation plugins are possible.
        'plugin_type':     'sim'
    }

    return config


class JasonCR(ConflictResolution):
    def __init__(self):
        super().__init__()
        self.my_variable = None
    
    def resolve(self, conf, ownship, intruder):
        # Get all the values from CD that we would need
        confpairs = conf.confpairs # Pair IDs in conflict
        predicted_waypoints = conf.predicted_waypoints # Linestring of aircraft intent per pair
        qdr_mat = conf.qdr_mat # QDR for all aircraft
        dist_mat = conf.dist_mat # Distance for all aircraft
        
        # Copies of aircraft autopilot stuff
        newgs       = np.copy(ownship.ap.tas)
        newvs       = np.copy(ownship.ap.vs)
        newalt      = np.copy(ownship.ap.alt)
        newtrack    = np.copy(ownship.ap.trk)
        
        for pair_idx, pair in enumerate(confpairs):
            # Get the aircraft IDX
            ownship_idx = bs.traf.id.index(pair[0])
            intruder_idx = bs.traf.id.index(pair[1])
            
            # Get the new speeds for the ownship. 
            # Don't forget that conflict pairs includes both (idx1, idx2) and 
            # (idx2, idx1), so only give a command for the first aircraft in the pair.
            new_ownship_spd = self.JasonResolve(conf, ownship_idx, intruder_idx, predicted_waypoints, qdr_mat, dist_mat)
            newgs[ownship_idx] = new_ownship_spd
        
        return newtrack, newgs, newvs, newalt

    def JasonResolve(self, conf, ownship_idx, intruder_idx, predicted_waypoints, qdr_mat, dist_mat):
        # Just make it stop (horrible idea if left like this, all aircraft will stop)
        return 0
    
    # We want to override the HDGACTIVE flag for aircraft to always follow the heading from AP
    @property
    def hdgactive(self):
        ''' Return a boolean array sized according to the number of aircraft
            with True for all elements where heading is currently controlled by
            the conflict resolution algorithm.
        '''
        return np.array([False] * len(self.active))
    
    @property
    def vsactive(self):
        ''' Return a boolean array sized according to the number of aircraft
            with True for all elements where heading is currently controlled by
            the conflict resolution algorithm.
        '''
        return np.array([False] * len(self.active))
    
    @property
    def altactive(self):
        ''' Return a boolean array sized according to the number of aircraft
            with True for all elements where heading is currently controlled by
            the conflict resolution algorithm.
        '''
        return np.array([False] * len(self.active))
    
    # Need to overwrite resumenav
    def resumenav(self, conf, ownship, intruder):
        '''
            Decide for each aircraft in the conflict list whether the ASAS
            should be followed or not, based on if the aircraft pairs passed
            their CPA.
        '''
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
                self.stopping_dict.pop(bs.traf.id[idx1] + bs.traf.id[idx2], False)
                continue

            if idx2 >= 0:
                # Distance vector using flat earth approximation
                re = 6371000.
                dist = re * np.array([np.radians(intruder.lon[idx2] - ownship.lon[idx1]) *
                                      np.cos(0.5 * np.radians(intruder.lat[idx2] +
                                                              ownship.lat[idx1])),
                                      np.radians(intruder.lat[idx2] - ownship.lat[idx1])])

                # Relative velocity vector
                vrel = np.array([intruder.gseast[idx2] - ownship.gseast[idx1],
                                 intruder.gsnorth[idx2] - ownship.gsnorth[idx1]])

                # Check if conflict is past CPA
                past_cpa = np.dot(dist, vrel) > 0.0
                
                ###### ANDREI'S CHANGE ###############
                # Also check the distance between aircraft
                distance = self.norm(dist)
                # We want enough distance between aircraft
                dist_ok = (distance > 2*bs.traf.cd.rpz_def) 
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
                is_bouncing = \
                    abs(anglediff(ownship.trk[idx1], intruder.trk[idx2])) < 30.0 and \
                    hdist < rpz * self.resofach

            # Start recovery for ownship if intruder is deleted, or if past CPA
            # and not in horizontal LOS or a bouncing conflict
            if idx2 >= 0 and (not past_cpa or hor_los or is_bouncing or dist_ok):
                ##### ANDREI'S CHANGE -> also added the dist_ok here ----  ^
                # Enable ASAS for this aircraft
                changeactive[idx1] = True
            else:
                # Switch ASAS off for ownship if there are no other conflicts
                # that this aircraft is involved in.
                changeactive[idx1] = changeactive.get(idx1, False)
                # If conflict is solved, remove it from the resopairs list
                delpairs.add(conflict)
                # Remove this pair from the stopping dict
                self.stopping_dict.pop(bs.traf.id[idx1] + bs.traf.id[idx2], False)

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
                        idx, bs.traf.ap.route[idx].wpname[iwpid])

        # Remove pairs from the list that are past CPA or have deleted aircraft
        self.resopairs -= delpairs