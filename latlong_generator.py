"""
        File Name: latlong_generator.py
        Author: Brian Ko (swko2@illinois.edu)
        Maintainer: Brian Ko (swko2@illinois.edu)
        Description:
            This script subdivides a given area in Cairo, Egypt into specified
            x by x grid, and y latitude/longitude pairs will be randomly
            sampled from each cells of the grid.
            a---------x---------x---------b
            |         |         |         |
            |  (2,0)  |  (2,1)  |  (2,2)  |
            |         |         |         |
            x---------x---------x---------x
            |         |         |         |
            |  (1,0)  |  (1,1)  |  (1,2)  |
            |         |         |         |
            x---------x---------x---------x
            |         |         |         |
            |  (0,0)  |  (0,1)  |  (0,2)  |
            |         |         |         |
            c---------x---------x---------d
            a, b, c, and d are the lat/longs of the top-left, top-right,
            bottom-left, and bottom-right, respectively. In this case, x = 3,
            hence the 3x3 grid.
"""

import random
import logging
#import matplotlib.pyplot as plt
#import pymongo
#from geopy.distance import geodesic

# Lat/Longs of each four corners of interested square area of Cairo, Egypt
TOP_LEFT = (30.1492, 31.246)
TOP_RIGHT = (30.1492, 31.446)
BOT_LEFT = (29.975, 31.246)
BOT_RIGHT = (29.975, 31.446)
CENTER = (30.0621, 31.346)

#print("Top Left Lat/Long: {0}".format(TOP_LEFT))
#print("Top Right Lat/Long: {0}".format(TOP_RIGHT))
#print("Bottom Left Lat/Long: {0}".format(BOT_LEFT))
#print("Bottom Right Lat/Long: {0}".format(BOT_RIGHT))
#print("TOP DISTANCE: {0}".format(geodesic(TOP_LEFT, TOP_RIGHT).miles))
#print("BOT DISTANCE: {0}".format(geodesic(BOT_LEFT, BOT_RIGHT).miles))
#print("LEFT DISTANCE: {0}".format(geodesic(TOP_LEFT, BOT_LEFT).miles))
#print("RIGHT DISTANCE: {0}".format(geodesic(TOP_RIGHT, BOT_RIGHT).miles))

def generate_cells(amt=20, t_l=TOP_LEFT, t_r=TOP_RIGHT, b_l=BOT_LEFT, b_r=BOT_RIGHT):
    """Subdivides interested square area into specified x by x
    Uses the given lat/long pairs of each four corners of the square area and
    the amount x given by the parameter to divide said area into x by x grid.
    Args:
        amt: The amount of cells in the columns AND rows.
        t_l: The lat/long of the top-left corner
        t_r: The lat/long of the top-right corner
        b_l: The lat/long of the bottom-left corner
        b_r: The lat/long of the bottom-right corner
    Returns:
        cells: A dictionary in which keys are the (x,y) coordinate of the cell
               and the values are the lat/longs of the bottom-left and top-
               right corner of the corresponding cell.
    """

    # Set bottom-left as the base to which to add increments
    lats = [b_l[0]]*(amt+1)
    longs = [b_l[1]]*(amt+1)

    lat_diff = t_l[0]-b_l[0]
    long_diff = b_r[1]-b_l[1]

    # Generate lat/long points by adding small, consistent increments
    lats = [(l + lat_diff*x/amt) for x, l in enumerate(lats)]
    longs = [(l + long_diff*x/amt) for x, l in enumerate(longs)]

    cells = []

    for x in range(len(lats)-1):
        for y in range(len(longs)-1):
            latlong = []
            latlong.append((lats[x],longs[y]))
            latlong.append((lats[x+1],longs[y+1]))
            latlongs_dict = {}
            latlongs_dict["coord"] = (x,y)
            latlongs_dict["latlongs"] = latlong
            cells.append(latlongs_dict)

    return cells

def generate_latlongs(amt=10):
    """Generates specified amount of random lat/longs from every cells
    Randomly samples a specified amount of lat/long pairs from every single
    cells and returns each set of lat/longs with its corresponding coordinates
    in dictionary form.
    Args:
        amt: The amount of samples to take in each cell.
    Returns:
        latlong_list: A list of dictionaries, each of which contains key-value
                      pairs of coordinates and a set of randomly sampled
                      lat/long pairs.
    """

    random.seed(0) # Seeded for testing purposes
    cells = generate_cells()
    latlong_list = []

    # Generate dictionaries of every cell's respective coordinates and set of
    # lat/long pairs
    for cell in cells:
        coord = cell["coord"]
        latlong = cell["latlongs"]
        lats = [latlong[0][0], latlong[1][0]]
        longs = [latlong[0][1], latlong[1][1]]
        latlong_dict = {}
        latlongs_orig = []
        latlongs_dest = []

        # Randomly sample 'amt' amount of lat/long pairs
        for _ in range(amt/2):
            latitude_o = random.uniform(*lats)
            longitude_o = random.uniform(*longs)
            latitude_d = random.uniform(*lats)
            longitude_d = random.uniform(*longs)
            latlongs_orig.append([latitude_o, longitude_o])
            latlongs_dest.append([latitude_d, longitude_d])
        latlong_dict["coord"] = coord
        latlong_dict["latlongs_o"] = latlongs_orig
        latlong_dict["latlongs_d"] = latlongs_dest
        latlong_list.append(latlong_dict)

    return latlong_list
