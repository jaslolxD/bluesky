import bluesky as bs
from bluesky import stack
from bluesky.traffic import Route
from bluesky.core import Entity, timed_function
from bluesky.stack import command
from bluesky.tools.aero import kts, ft, nm, fpm
from bluesky.tools.geo import kwikqdrdist, kwikpos, kwikdist, kwikdist_matrix
from bluesky.tools.misc import degto180
from shapely.geometry import LineString
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
    config = {"plugin_name": "TRAFFICSPAWNER", "plugin_type": "sim", "reset": reset}
    # Put TrafficSpawner in bs.traf
    bs.traf.TrafficSpawner = trafficSpawner()
    return config


def reset():
    bs.traf.TrafficSpawner.reset()


class trafficSpawner(Entity):
    def __init__(self):
        super().__init__()
        self.target_ntraf = 50
        self.traf_id = 1
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

    def create(self, n=1):
        super().create(n)
        # Store creation time of new aircraft
        self.route_edges[-n:] = [0] * n  # Default edge
        self.distance2D[-n:] = [0] * n
        self.distance3D[-n:] = [0] * n
        self.distancealt[-n:] = [0] * n
        self.create_time[-n:] = [0] * n

    @timed_function(dt=1)
    def spawn(self):
        routes = os.listdir(
            f"bluesky/plugins/graph_genetic_algorithm/pickles"
        )
        # random.seed(1)
        attempts = 0
        while bs.traf.ntraf < self.target_ntraf and attempts < 100:
            count = 0
            dangerclose = False
            route_entry = random.randint(0, len(routes) - 1)
            filename = routes[route_entry]
            #filename = "3582-2692.pkl"
            route = pd.read_pickle(
                f"bluesky/plugins/graph_genetic_algorithm/pickles/{filename}"
            )
            lats, lons = zip(*route)
            dist = kwikdist_matrix(
                np.array([lats[0]]), np.array([lons[0]]), bs.traf.lat, bs.traf.lon
            )
            dist = dist * nm

            if np.any(dist < 64):
                #print("TOO CLOSE")
                #bs.scr.echo("TOO CLOSE")
                attempts += 1
                continue

            acid = f"DR{self.traf_id}"
            #if acid == "DR24":
            #    print(filename)
            self.traf_id += 1
            actype = "M600"
            achdg, _ = kwikqdrdist(lats[0], lons[0], lats[1], lons[1])
            bs.traf.cre(acid, actype, lats[0], lons[0], achdg, self.traf_alt, 20 * kts)
            acrte = Route._routes.get(acid)
            acidx = bs.traf.id.index(acid)
            #bs.scr.echo(f"spawning")
            lastwp = []
            for i in range(len(route)):
                if i == len(route) - 1:
                    acrte.swflyby = True
                    acrte.swflyturn = False
                    wptype = Route.wplatlon
                    acrte.addwpt_simple(
                        acidx,
                        f"WP{count}",
                        wptype,
                        route[i][0],
                        route[i][1],
                        self.traf_alt,
                        20 * kts,
                    )
                elif i == 0:
                    future_angle = achdg
                    acrte.swflyby = True
                    acrte.swflyturn = False
                    wptype = Route.wplatlon
                    acrte.addwpt_simple(
                        acidx,
                        f"WP{count}",
                        wptype,
                        route[i][0],
                        route[i][1],
                        self.traf_alt,
                        20 * kts,
                    )
                else:
                    future_angle, _ = kwikqdrdist(
                        route[i][0], route[i][1], route[i + 1][0], route[i + 1][1]
                    )
                    angle = current_angle - future_angle
                    #Here
                    if abs((angle + 180) % 360 - 180) > 50:
                        acrte.swflyby = False
                        acrte.swflyturn = True
                        acrte.turnspd = 5 * kts
                        wptype = Route.wplatlon
                        acrte.addwpt_simple(
                            acidx,
                            f"WP{count}",
                            wptype,
                            route[i][0],
                            route[i][1],
                            self.traf_alt,
                            5 * kts,
                        )
                    else:
                        acrte.swflyby = True
                        acrte.swflyturn = False
                        wptype = Route.wplatlon
                        acrte.addwpt_simple(
                            acidx,
                            f"WP{count}",
                            wptype,
                            route[i][0],
                            route[i][1],
                            self.traf_alt,
                            20 * kts,
                        )
                current_angle = future_angle
                count += 1
            acrte.calcfp()
            stack.stack(f"DIRECT {acid} WP0")
            stack.stack(f"LNAV {acid} ON")
            stack.stack(f"VNAV {acid} ON")
            self.create_time[acidx] = bs.sim.simt

    # @timed_function(dt = 10)
    def printer(self):
        try:
            bs.traf.id
        except:
            #bs.scr.echo("this doesnt work")
            return
        else:
            acids = bs.traf.id

        for acid in acids:
            time = 0
            acidx = bs.traf.id2idx(acid)
            acrte = Route._routes.get(acid)

            #bs.scr.echo(f" lat: {bs.traf.lat[acidx]} lon: {bs.traf.lon[acidx]}")

        stack.stack("HOLD")
        
    @command
    def trafficnumber(self, target_traf = 50):
        self.target_ntraf = int(target_traf)
        #bs.scr.echo(f"Traffic number has been set to {int(target_traf)}")
        return
        
        

    @timed_function(dt=0.5)
    def delete_aircraft(self):
        self.update_logging()
        # Delete aircraft that have LNAV off and have gone past the last waypoint.
        lnav_on = bs.traf.swlnav
        still_going_to_dest = np.logical_and(
            abs(degto180(bs.traf.trk - bs.traf.ap.qdr2wp)) < 10.0,
            bs.traf.ap.dist2wp > 5,
        )
        delete_array = np.logical_and.reduce(
            (
                np.logical_not(lnav_on),
                bs.traf.actwp.swlastwp,
                np.logical_not(still_going_to_dest),
            )
        )

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
                    bs.traf.alt[idx] / ft,
                    bs.traf.tas[idx] / kts,
                    bs.traf.vs[idx] / fpm,
                    bs.traf.hdg[idx],
                    bs.traf.cr.active[idx],
                    bs.traf.aporasas.alt[idx] / ft,
                    bs.traf.aporasas.tas[idx] / kts,
                    bs.traf.aporasas.vs[idx] / fpm,
                    bs.traf.aporasas.hdg[idx],
                )
                bs.traf.delete(idx)
                # stack.stack(f'DEL {acid}')

    def update_logging(self):
        # Increment the distance metrics
        resultantspd = np.sqrt(bs.traf.gs * bs.traf.gs + bs.traf.vs * bs.traf.vs)
        self.distance2D += bs.sim.simdt * abs(bs.traf.gs)
        self.distance3D += bs.sim.simdt * resultantspd
        self.distancealt += bs.sim.simdt * abs(bs.traf.vs)

        # Now let's do the CONF and LOS logs
        confpairs_new = list(set(bs.traf.cd.confpairs) - self.prevconfpairs)
        if confpairs_new:
            done_pairs = []
            for pair in set(confpairs_new):
                # Check if the aircraft still exist
                if (pair[0] in bs.traf.id) and (pair[1] in bs.traf.id):
                    # Get the two aircraft
                    idx1 = bs.traf.id.index(pair[0])
                    idx2 = bs.traf.id.index(pair[1])
                    done_pairs.append((idx1, idx2))
                    if (idx2, idx1) in done_pairs:
                        continue

                    bs.traf.CDLogger.conflog.log(
                        pair[0],
                        pair[1],
                        bs.traf.lat[idx1],
                        bs.traf.lon[idx1],
                        bs.traf.alt[idx1],
                        bs.traf.lat[idx2],
                        bs.traf.lon[idx2],
                        bs.traf.alt[idx2],
                    )

        self.prevconfpairs = set(bs.traf.cd.confpairs)

        # Losses of separation as well
        # We want to track the LOS, and log the minimum distance and altitude between these two aircraft.
        # This gives us the lospairs that were here previously but aren't anymore
        lospairs_out = list(self.prevlospairs - set(bs.traf.cd.lospairs))

        # Attempt to calculate current distance for all current lospairs, and store it in the dictionary
        # if entry doesn't exist yet or if calculated distance is smaller.
        for pair in bs.traf.cd.lospairs:
            # Check if the aircraft still exist
            if (pair[0] in bs.traf.id) and (pair[1] in bs.traf.id):
                idx1 = bs.traf.id.index(pair[0])
                idx2 = bs.traf.id.index(pair[1])
                # Check if the routes of these two aircraft intersect
                intersects = self.route_intersect(idx1, idx2)
                # Calculate current distance between them [m]
                losdistance = (
                    kwikdist(
                        bs.traf.lat[idx1],
                        bs.traf.lon[idx1],
                        bs.traf.lat[idx2],
                        bs.traf.lon[idx2],
                    )
                    * nm
                )
                # To avoid repeats, the dictionary entry is DxDy, where x<y. So D32 and D564 would be D32D564
                dictkey = (
                    pair[0] + pair[1]
                    if int(pair[0][2:]) < int(pair[1][2:])
                    else pair[1] + pair[0]
                )
                if dictkey not in self.losmindist:
                    # Set the entry
                    self.losmindist[dictkey] = [
                        losdistance,
                        bs.traf.lat[idx1],
                        bs.traf.lon[idx1],
                        bs.traf.alt[idx1],
                        bs.traf.lat[idx2],
                        bs.traf.lon[idx2],
                        bs.traf.alt[idx2],
                        bs.sim.simt,
                        bs.sim.simt,
                        intersects
                    ]
                    # This guy here                             ^ is the LOS start time
                else:
                    # Entry exists, check if calculated is smaller
                    if self.losmindist[dictkey][0] > losdistance:
                        # It's smaller. Make sure to keep the LOS start time
                        self.losmindist[dictkey] = [
                            losdistance,
                            bs.traf.lat[idx1],
                            bs.traf.lon[idx1],
                            bs.traf.alt[idx1],
                            bs.traf.lat[idx2],
                            bs.traf.lon[idx2],
                            bs.traf.alt[idx2],
                            bs.sim.simt,
                            self.losmindist[dictkey][8],
                            intersects
                        ]

        # Log data if there are aircraft that are no longer in LOS
        if lospairs_out:
            done_pairs = []
            for pair in set(lospairs_out):
                # Get their dictkey
                dictkey = (
                    pair[0] + pair[1]
                    if int(pair[0][2:]) < int(pair[1][2:])
                    else pair[1] + pair[0]
                )
                # Is this pair in the dictionary?
                if dictkey not in self.losmindist:
                    # Pair was already logged, continue
                    continue
                losdata = self.losmindist[dictkey]
                # Remove this aircraft pair from losmindist
                self.losmindist.pop(dictkey)
                # Log the LOS
                bs.traf.CDLogger.loslog.log(
                    losdata[8],
                    losdata[7],
                    pair[0],
                    pair[1],
                    losdata[1],
                    losdata[2],
                    losdata[3],
                    losdata[4],
                    losdata[5],
                    losdata[6],
                    losdata[0],
                    losdata[-1]
                )

        self.prevlospairs = set(bs.traf.cd.lospairs)

    def reset(self):
        self.target_ntraf = 50
        self.traf_id = 1
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
    
    def route_intersect(self, idx1, idx2):
        # Get the clipped routes
        clip1 = self.clip_route(idx1, 100, 100)
        clip2 = self.clip_route(idx2, 100, 100)
        # Get shapely lines
        line1 = LineString(clip1)
        line2 = LineString(clip2)
        return line1.intersects(line2)
            
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
            back_wp_list.append((prevwp[1], prevwp[0]))
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
            front_wp_list.append((nextwp[1], nextwp[0]))
            # Set new wp
            i += 1
            currentwp = nextwp
            
        # Put the list together
        return back_wp_list + [(bs.traf.lon[idx], bs.traf.lat[idx])] + front_wp_list


def distaccel(v0, v1, axabs):
    """Calculate distance travelled during acceleration/deceleration
    v0 = start speed, v1 = endspeed, axabs = magnitude of accel/decel
    accel/decel is detemremind by sign of v1-v0
    axabs is acceleration/deceleration of which absolute value will be used
    solve for x: x = vo*t + 1/2*a*t*t    v = v0 + a*t"""
    return 0.5 * np.abs(v1 * v1 - v0 * v0) / np.maximum(0.001, np.abs(axabs))
