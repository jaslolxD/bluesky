import numpy as np
import pandas as pd

nm  = 1852.  
def kwikqdrdist_matrix(lata, lona, latb, lonb):
    """Gives quick and dirty qdr[deg] and dist [nm] matrices
       from lat/lon vectors. (note: does not work well close to poles)"""

    re      = 6371000.  # radius earth [m]
    dlat    = np.radians(latb - lata.T)
    dlon    = np.radians(((lonb - lona.T)+ 180) % 360 - 180)
    cavelat = np.cos(np.radians(latb + lata.T) * 0.5)

    dangle  = np.sqrt(np.multiply(dlat, dlat) +
                      np.multiply(np.multiply(dlon, dlon),
                                  np.multiply(cavelat, cavelat)))
    dist    = re * dangle / nm

    qdr     = np.degrees(np.arctan2(np.multiply(dlon, cavelat), dlat)) % 360.

    return qdr, dist


array_measurement= [['DR1', 1, 40.80586699999998, -73.9528064], ['DR1', 2, 40.80559163329035, -73.95215093989852], ['DR1', 3, 40.80525466492582, -73.95134874391279], ['DR2', 1, 40.709984204438584, -73.99482690372832], ['DR2', 2, 40.71014249999999, -73.9940887], ['DR2', 3, 40.71038585131503, -73.99412271512116]]
confpair =[]
df = pd.DataFrame(array_measurement, columns=["acid", "part", "lat", "lon"])
I = I = np.eye(len(df["acid"].unique()))
parts = max(df["part"])
print(parts)

for i in range(1, parts+1):
    qdr,dist = kwikqdrdist_matrix(np.asmatrix(df[df["part"] ==i ].lat),np.asmatrix(df[df["part"] ==i ].lon), np.asmatrix(df[df["part"] ==i ].lat), np.asmatrix(df[df["part"] ==i ].lon))
    qdr = np.asarray(qdr)
    dist = np.asarray(dist) * nm + 1e9 * I
    conflicts = np.column_stack(np.where(dist < 100000))
    print(i)
    for pair in conflicts:
        print(pair[0])
        confpair.append((df["acid"].unique()[pair[0]], df["acid"].unique()[pair[1]]))
    print(confpair)
    

#I = I = np.eye(2)
#array_measurement= [['DR1', 1, 40.80586699999998, -73.9528064], ['DR1', 2, 40.80559163329035, -73.95215093989852], ['DR1', 3, 40.80525466492582, -73.95134874391279], ['DR2', 1, 40.709984204438584, -73.99482690372832], ['DR2', 2, 40.71014249999999, -73.9940887], ['DR2', 3, 40.71038585131503, -73.99412271512116]]
#arr = np.array(array_measurement)
#arr = arr.astype("object")
##arr = array_measurement[np.where(array_measurement[:][1] == 1)]
#arr[:,1] = arr[:,1].astype(int)
#arr[:,2:4] = arr[:,2:4].astype(float)
#first_arr = arr[np.where(arr[:,1] == 1)]
#
#
#qdr, dist = kwikqdrdist_matrix(np.asmatrix(first_arr[:,2]), np.asmatrix(first_arr[:,3]),np.asmatrix(first_arr[:,2]), np.asmatrix(first_arr[:,3]))
#qdr = np.asarray(qdr)
#dist = np.asarray(dist) * nm + 1e9 * I
#print(dist)
        






#Code of route_checker

#    @timed_function(dt = 30)
#    def route_checker(self):
#        try:
#            bs.traf.id
#        except:
#            bs.scr.echo("this doesnt work")
#            return
#        else:
#            acids = bs.traf.id
#
#        for acid in acids:
#            time = 0
#            acidx = bs.traf.id2idx(acid)
#            acrte = Route._routes.get(acid)
#            current_wp = acrte.iactwp
#            first_run = True
#            start_turn = False
#            floor_div = 0
#            measurement_freq= 10
#            array_measurement= []
#            while time < 30:
#                if first_run == True:
#                    _, dist = kwikqdrdist(bs.traf.lat[acidx], bs.traf.lon[acidx], acrte.wplat[current_wp], acrte.wplon[current_wp])
#                    dist *= nm
#
#                    #Drone going towards a turn in the first run
#                    if acrte.wpflyturn[current_wp] == True:
#                        wpqdr, _ = kwikqdrdist(acrte.wplat[current_wp -1], acrte.wplon[current_wp -1], acrte.wplat[current_wp], acrte.wplon[current_wp])
#                        nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp], acrte.wplon[current_wp], acrte.wplat[current_wp +1], acrte.wplon[current_wp +1])
#                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
#                        accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
#                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
#                    
#                        if dist > turndist + accel_dist:
#                            #Cruise distance
#                            cruise_dist = dist - accel_dist - turndist 
#                            cruise_time = cruise_dist / (15*kts)
#
#                            #Deceleration time
#                            accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                            #No turn time since turn is made for the second waypoint
#                            start_turn = True
#
#                            #Add it all up
#                            time_diff = cruise_time + accel_time
#                            time += time_diff
#
#                            #bs.scr.echo(f"Initial turn Cruise region time: {time}")
#
#                        else:
#
#                            #deceleration time
#                            accel_time = abs(bs.traf.tas[acidx] - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                            #Turn time half cuz only till current_wp
#                            start_turn = True
#
#                            #Add it all up
#                            time_diff = accel_time
#                            time += time_diff
#
#                            #bs.scr.echo(f"Initial turn Decell region time: {time}")
#
#
#                    #Drone going away from a turn in the first run
#                    elif acrte.wpflyturn[current_wp-1] == True:
#                        wpqdr, _ = kwikqdrdist(acrte.wplat[current_wp -2], acrte.wplon[current_wp -2], acrte.wplat[current_wp-1], acrte.wplon[current_wp-1])
#                        nextwpqdr, leg_dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
#                        leg_dist = leg_dist *nm
#                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
#                        accel_dist = distaccel( 5*kts, 15*kts, bs.traf.perf.axmax[acidx])
#                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
#                        cruise_dist = leg_dist - accel_dist - turndist
#                        
#
#                        if dist < accel_dist:
#                            #acceleration time
#                            accel_time = abs(bs.traf.tas[acidx] - 15*kts)/ bs.traf.perf.axmax[acidx]
#
#                            time_diff = accel_time
#                            time += time_diff
#
#                        elif dist < accel_dist + cruise_dist:
#                            #acceleration time
#                            accel_time = abs(15* kts - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                            #cruise time
#                            partial_cruise_dist = dist - accel_dist
#                            cruise_time = partial_cruise_dist / (5*kts)
#
#                            #Add it all up
#                            time_diff = cruise_time + accel_time
#                            time += time_diff
#
#                        else: 
#                            #acceleration time
#                            accel_time = abs(15* kts - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                            #cruise time
#                            cruise_time = cruise_dist / (5*kts)
#
#                            #Turning time
#                            turn_time = turning_dist * 0.5/ (5*kts)
#
#                            #Add it all up
#                            time_diff = cruise_time + accel_time + turn_time
#                            time += time_diff
#                            
#                    #Regular cruise
#                    else:
#                        time += dist/ (15*kts)
#
#                    first_run = False
#                    current_wp +=1
#
#                #Iterations after turn
#                elif start_turn == True:
#                    if acrte.wpflyturn[current_wp] == True:
#                        #second part of initial turn
#                        initial_turn_time = turning_dist/ (5*kts)
#                        initial_turndist = turndist
#
#                        #Calculations for the second turn parameters
#                        wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -1], acrte.wplon[current_wp -1], acrte.wplat[current_wp], acrte.wplon[current_wp])
#                        dist = dist *nm
#                        nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp], acrte.wplon[current_wp], acrte.wplat[current_wp +1], acrte.wplon[current_wp +1])
#                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
#
#                        #Calculate the leg distance, acceleration distance and turning distance (total distance covered by turn) for second turn
#                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
#
#                        #Cruise distance with turning speed instead of cruise
#                        cruise_dist = dist - turndist - initial_turndist
#                        cruise_time = cruise_dist / (5*kts)
#
#                        # Second turn time times half cuz only till current_wp
#                        start_turn = True
#
#                        #Total time
#                        time_diff = initial_turn_time + cruise_time 
#                        time += time_diff
#                        
#                        current_wp +=1
#
#
#                    else:
#                        #The turn
#                        turn_time = turning_dist/ (5*kts)
#
#                        #Acceleration
#                        accel_dist = distaccel(5*kts, 15*kts, bs.traf.perf.axmax[acidx])
#                        accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                        #Cruise whilst still being in turning speed
#                        _ , dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
#                        dist = dist * nm
#                        cruise_dist = dist - accel_dist - turndist
#                        cruise_time = cruise_dist / (5*kts)
#
#                        #Total time
#                        time_diff = cruise_time + accel_time + turn_time
#                        time += time_diff
#                        
#                        start_turn = False
#                        current_wp +=1
#
#                #Iterations after a regular leg
#                else:
#                    if acrte.wpflyturn[current_wp] == True:
#                        wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -1], acrte.wplon[current_wp -1], acrte.wplat[current_wp], acrte.wplon[current_wp])
#                        dist = dist *nm
#                        nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp], acrte.wplon[current_wp], acrte.wplat[current_wp +1], acrte.wplon[current_wp +1])
#                        turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
#                        
#                        #Calculate the leg distance, acceleration distance and turning distance (total distance covered by turn)
#                        accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
#                        turning_dist = abs(2*np.pi*turnrad * hdgchange/360)
#                        
#                        #Cruise distance
#                        cruise_dist = dist - accel_dist - turndist 
#                        cruise_time = cruise_dist / (15*kts)
#
#                        #Deceleration time
#                        accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                        #Turn  time times half cuz only till current_wp
#                        start_turn = True
#
#                        #Add it all up
#                        time_diff = cruise_time + accel_time
#                        time += time_diff
#  
#                        current_wp +=1
#                    
#                    else:
#                        _ , dist = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp], acrte.wplon[current_wp])
#                        dist = dist *nm
#                        time_diff = dist / (15*kts)
#                        time += time_diff                    
#                        current_wp +=1
#
#        #--------------------------------------------------------------------------------------------------------------------------------------------------
#            #Position Calculations
#                if floor_div < time // measurement_freq:
#                    i= 0
#                    value = int(time // measurement_freq) - floor_div
#                    while i < value and floor_div < 3:
#                        floor_div += 1
#                        overshoot_time = time - floor_div * measurement_freq
#                        print(f"overshoot_time: {overshoot_time}")
#                        print(f"floor_div: {floor_div}")
#                        print(i)
#
#                        if acrte.wpflyturn[current_wp-1] == True:
#                            wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -2], acrte.wplon[current_wp -2], acrte.wplat[current_wp-1], acrte.wplon[current_wp-1])
#                            dist = dist *nm
#                            nextwpqdr, _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp ], acrte.wplon[current_wp])
#                            turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
#
#                            accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
#                            accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                            #Ends in deceleration part before turn
#                            if overshoot_time < accel_time:
#                                overshoot_dist = 0.5 * bs.traf.perf.axmax[acidx] * (overshoot_time)**2 + 5 * kts * overshoot_time
#                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
#                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)
#
#                            #Ends in cruise part before turn
#                            else: 
#                                remaining_time = overshoot_time - accel_time
#                                overshoot_dist = accel_dist + remaining_time * 15*kts
#                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
#                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)
#
#
#
#                        elif acrte.wpflyturn[current_wp-2] == True:
#                            wpqdr, dist = kwikqdrdist(acrte.wplat[current_wp -3], acrte.wplon[current_wp -3], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
#                            dist = dist *nm
#                            nextwpqdr, leg_dist = kwikqdrdist(acrte.wplat[current_wp-2], acrte.wplon[current_wp-2], acrte.wplat[current_wp-1], acrte.wplon[current_wp-1])
#                            leg_dist *= nm
#                            turndist, turnrad, hdgchange= bs.traf.actwp.kwikcalcturn( 5*kts, 25, wpqdr, nextwpqdr)
#
#                            accel_dist = distaccel(15*kts, 5*kts, bs.traf.perf.axmax[acidx])
#                            accel_time = abs(15*kts - 5*kts)/ bs.traf.perf.axmax[acidx]
#
#                            cruise_dist = leg_dist - turndist - accel_dist
#                            cruise_time = cruise_dist / 5 *kts
#
#                            if overshoot_time < accel_time:
#                                overshoot_dist = - 0.5 * bs.traf.perf.axmax[acidx] * (overshoot_time)**2 + 15 * kts * overshoot_time
#                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
#                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)
#
#                            elif overshoot_time < accel_time + cruise_time:
#                                remaining_time = overshoot_time - accel_time
#                                overshoot_dist = accel_dist + remaining_time * 5*kts
#                                bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
#                                final_lat , final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)
#
#
#                            else:
#                                final_lat = acrte.wplat[current_wp -2]
#                                final_lon = acrte.wplon[current_wp -2]
#
#
#                        else:
#                            overshoot_dist = overshoot_time * 15*kts
#                            bearing , _ = kwikqdrdist(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], acrte.wplat[current_wp-2], acrte.wplon[current_wp-2])
#                            final_lat, final_lon = kwikpos(acrte.wplat[current_wp-1], acrte.wplon[current_wp-1], bearing, overshoot_dist/nm)
#
#                        #Data record
#                        array_measurement.append([acid, floor_div, final_lat, final_lon])
#                        i +=1
#
#                    print(f"time: {time} and floor div {floor_div}") 
#                    print("---------------------------------------------------------------")
#                        #bs.scr.echo(f"Currented location {floor_div}:     {bs.traf.lat[acidx]} {bs.traf.lon[acidx]}")
#
#
#            #Print stuff
#            #bs.scr.echo(f"------------------------------------------------------------------------------------")
#            #bs.scr.echo(f"Current wp: {current_wp -1} and {acrte.wplat[current_wp-1]} {acrte.wplon[current_wp-1]}")
#            #bs.scr.echo(f"Predicted location:   {final_lat} {final_lon}")
#            #bs.scr.echo(f"Overshoot dist {overshoot_dist}")
#            #bs.scr.echo(f"Bearing {bearing}")
#            #bs.scr.echo(f"Going to waypoint now: {acrte.iactwp}")
#            #bs.scr.echo(f"Waypoint predicted: {current_wp -1}")
#            #bs.scr.echo(f"Next turn distance {bs.traf.actwp.turndist[acidx]}")
#            #bs.scr.echo(f"Turnadius {bs.traf.actwp.nextturnrad[acidx]}")
#            #bs.scr.echo(f"Turn wp index {bs.traf.actwp.nextturnidx[acidx]}")
#            #bs.scr.echo(f"Turn Distance {turndist}")
#            #bs.scr.echo(f"Turn Radius {turnrad}")
#            #bs.scr.echo(f"inital angle is {wpqdr}")
#            #bs.scr.echo(f"second angle is {nextwpqdr}")
#        bs.scr.echo(f"{array_measurement}")
#        stack.stack(f"HOLD")    