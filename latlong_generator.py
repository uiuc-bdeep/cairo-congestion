import random
import pymongo
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from geopy.distance import geodesic

TOP_LEFT = (30.1492, 31.246)
TOP_RIGHT = (30.1492, 31.446)
BOT_LEFT = (29.975, 31.246)
BOT_RIGHT = (29.975, 31.446)

print("TOP DISTANCE: {0}".format(geodesic(TOP_LEFT, TOP_RIGHT).miles))
print("BOT DISTANCE: {0}".format(geodesic(BOT_LEFT, BOT_RIGHT).miles))
print("LEFT DISTANCE: {0}".format(geodesic(TOP_LEFT, BOT_LEFT).miles))
print("RIGHT DISTANCE: {0}".format(geodesic(TOP_RIGHT, BOT_RIGHT).miles))

def generate_cells(amt=20):
    lats = [BOT_LEFT[0]]*(amt+1)
    longs = [BOT_LEFT[1]]*(amt+1)

    lat_diff = TOP_LEFT[0]-BOT_LEFT[0]
    long_diff = BOT_RIGHT[1]-BOT_LEFT[1]

    lats = [(l + lat_diff*x/amt) for x, l in enumerate(lats)]
    longs = [(l + long_diff*x/amt) for x, l in enumerate(longs)]

    latlongs = []

    for x in range(len(lats)-1):
        for y in range(len(longs)-1):
            latlong = []
            latlong.append((lats[x],longs[y]))
            latlong.append((lats[x+1],longs[y+1]))
            latlongs.append(latlong)

    return latlongs

def generate_coords(amt=10):
    random.seed(0)
    latlongs = generate_cells()
    coords_list = []

    for latlong in latlongs:
        coords = []
        lats = [latlong[0][0], latlong[1][0]]
        longs = [latlong[0][1], latlong[1][1]]
        for _ in range(amt):
            latitude = random.uniform(*lats)
            longitude = random.uniform(*longs)
            coords.append([latitude, longitude])
        coords_list.append(coords)
    return coords_list
