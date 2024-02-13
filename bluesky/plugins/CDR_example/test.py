import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import osmnx as ox
from collections import Counter
import os
import geopandas as gpd

directory_all = os.listdir(r"bluesky\plugins\Thesis_stuff\output_all1")

for file in directory_all:
    f= open(rf"bluesky\plugins\Thesis_stuff\output_all1\{file}")
    if "_CD_STATE_" in file:
        f.close()
        print(file)
        os.remove(rf"bluesky\plugins\Thesis_stuff\output_all1\{file}")

            

nm = 1852.0


def kwikqdrdist_matrix(lata, lona, latb, lonb):
    """Gives quick and dirty qdr[deg] and dist [nm] matrices
    from lat/lon vectors. (note: does not work well close to poles)"""

    re = 6371000.0  # radius earth [m]
    dlat = np.radians(latb - lata.T)
    dlon = np.radians(((lonb - lona.T) + 180) % 360 - 180)
    cavelat = np.cos(np.radians(latb + lata.T) * 0.5)

    dangle = np.sqrt(
        np.multiply(dlat, dlat)
        + np.multiply(np.multiply(dlon, dlon), np.multiply(cavelat, cavelat))
    )
    dist = re * dangle / nm

    qdr = np.degrees(np.arctan2(np.multiply(dlon, cavelat), dlat)) % 360.0

    return qdr, dist

def kwikqdrdist(lata, lona, latb, lonb):
    """Gives quick and dirty qdr[deg] and dist [nm]
       from lat/lon. (note: does not work well close to poles)"""

    re      = 6371000.  # radius earth [m]
    dlat    = np.radians(latb - lata)
    dlon    = np.radians(((lonb - lona)+180)%360-180)
    cavelat = np.cos(np.radians(lata + latb) * 0.5)

    dangle  = np.sqrt(dlat * dlat + dlon * dlon * cavelat * cavelat)
    dist    = re * dangle / nm

    qdr     = np.degrees(np.arctan2(dlon * cavelat, dlat)) % 360.

    return qdr, dist

def kwikpos(latd1, lond1, qdr, dist):
    """Fast, but quick and dirty, position calculation from vectors of reference position,
    bearing and distance using flat earth approximation
    In:
         latd1,lond1  [deg]   ref position(s)
         qdr          [deg]   bearing (vector) from 1 to 2
         dist         [nm]    distance (vector) between 1 and 2
    Out:
         latd2,lond2 [deg]
    Use for flat earth purposes e.g. flat display"""

    dx = dist * np.sin(np.radians(qdr))
    dy = dist * np.cos(np.radians(qdr))
    dlat = dy / 60.0
    dlon = dx / (np.maximum(0.01, 60.0 * np.cos(np.radians(latd1))))
    latd2 = latd1 + dlat
    lond2 = ((lond1 + dlon) + 180) % 360 - 180

    return latd2, lond2

def finalVaccel(dist, v0, axabs):
    return np.sqrt(2*axabs*dist + v0**2)



#print(finalVaccel(10,5,5))
#lat1 = 52.3836
#lon1= 4.0967
#
#lat2 , lon2 = kwikpos(lat1, lon1, 0, 0.25)
#lat3, lon3 = kwikpos(lat1, lon1, 90, 0.25)
#lat4, lon4 = kwikpos(lat1, lon1, 270, 0.25)
##print(f" Lat: {lat2}, Lon: {lon2}")
#print(f" Lat: {lat4}, Lon: {lon4}")

# THIS PICKLE IS FUCKED
#3582-2692.pkl
#coords_list = [(40.78045109999999, -73.9860353), (40.78054460000001, -73.9862482), (40.7806784, -73.9865628), (40.780697799999984, -73.9866368), (40.7807105, -73.986693), (40.780716299999995, -73.9867392), (40.78072020000002, -73.9867982), (40.78072070000002, -73.98686230000001), (40.7807181, -73.9869329), (40.78070840000001, -73.9869955)]
#print(coords_list.index((40.7806784, -73.9865628)))
#array_measurement = [
#    ["DR1", 1, 40.80586699999998, -73.9528064],
#    ["DR1", 2, 40.80559163329035, -73.95215093989852],
#    ["DR1", 3, 40.80525466492582, -73.95134874391279],
#    ["DR2", 1, 40.709984204438584, -73.99482690372832],
#    ["DR2", 2, 40.71014249999999, -73.9940887],
#    ["DR2", 3, 40.71038585131503, -73.99412271512116],
#]
#confpairs = []
#confinfo= []
#df = pd.DataFrame(array_measurement, columns=["acid", "part", "lat", "lon"])
#I = I = np.eye(len(df["acid"].unique()))
#parts = max(df["part"])
## print(df)
#
#for i in range(1, parts + 1):
#    qdr, dist = kwikqdrdist_matrix(
#        np.asmatrix(df[df["part"] == i].lat),
#        np.asmatrix(df[df["part"] == i].lon),
#        np.asmatrix(df[df["part"] == i].lat),
#        np.asmatrix(df[df["part"] == i].lon),
#    )
#    qdr = np.asarray(qdr)
#    dist = np.asarray(dist) * nm + 1e9 * I
#    conflicts = np.column_stack(np.where(dist < 100000))
##    print(conflicts)
##    print(qdr)
#    for pair in conflicts:
#        print(pair)
#        print(df[df["part"] == i].acid.unique())
#        conflictpair = (df[df["part"] == i].acid.unique()[pair[0]], df[df["part"] == i].acid.unique()[pair[1]])
#        if conflictpair not in confpairs:
#            confpairs.append(conflictpair)
#            confinfo.append([conflictpair, i])



#print(confinfo)
#print(df)
#for entry in confinfo:
#    qdr1, _ = kwikqdrdist( df[(df["acid"] == entry[0][0]) & (df["part"] == entry[1] -1)].lat, df[(df["acid"] == entry[0][0]) & (df["part"] == entry[1] -1)].lon, 
#                                  df[(df["acid"] == entry[0][0]) & (df["part"] == entry[1])].lat, df[(df["acid"] == entry[0][0]) & (df["part"] == entry[1])].lon 
#                                  )
#    print(df[(df["acid"] == entry[0][0]) & (df["part"] == entry[1])])
    #print(df.query(f"part == {entry[1]} & acid == {entry[0][0]}"))
    
#conflist= []
#for x,y in confpairs:
#    conflist.append(x)
#    
#confcounter = Counter(conflist)
#print(type(confcounter))
#
#print(confcounter["DR1"])
#print("CR it works on this")
