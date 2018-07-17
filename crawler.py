'''
    File Name: crawler.py
    Author: Zehao Chen (zehaoc2@illinois.edu)
    Maintainer: Zehao Chen (zehaoc2@illinois.edu)
    Description:
	This script parses data from the JSON Object to form a URL and then
        requests data from the Google API. The response data is updated in
        the corresponding trip in the database.
'''

# Import libraries.
import os
import json
import requests
import logging
import time
from datetime import datetime, timedelta
from pprint import pprint
from pymongo import MongoClient
from bson.objectid import ObjectId

API_key = "AIzaSyADEXdHuYJDPa2K5oSzBxAUxCGEzzRvzi0"

highway_origin = ['30.00883,30.98311', '30.04729,31.21164', '30.01589,31.22906', '30.0074,31.1378', '29.99924,31.11619', '29.99004,31.22926', '30.0406,31.27429', '29.98631,31.14014', '30.03543,31.19842','30.07392,31.22743', '30.05899,31.19005', '30.04491,31.1943', '30.0231,31.23099' , '30.04964,31.23498', '30.07804,31.27811', '30.04435,31.23404', '30.03878,31.24374', '30.01596,31.40257', '30.02239,31.25536', '30.00522,31.2723', '30.01171,31.21782', '30.04069,31.21996', '30.08082,31.449', '30.15221,31.43613', '30.05037,31.27541']

highway_destination = ['30.06227,31.1739', '30.05888,31.3027', '30.08064,31.31678', '29.98999,31.22891', '30.07043,31.0135', '29.99984,31.39549', '30.08006,31.36171', '30.01292,31.20846', '30.04417,31.24352', '29.96512,31.2431', '30.01489,31.20516', '30.06055,31.20855', '30.04361,31.23601', '30.05902,31.24447', '30.05657,31.24058', '30.03989,31.21812', '30.05234,31.24425', '30.02518,31.47312', '30.02464,31.25959', '29.96445,31.28756', '29.98798,31.21479', '30.07561,31.22305', '30.10563,31.6032', '30.12723,31.35643', '30.1057,31.36047']

def slack_notification(slack_msg):
    """
        Send slack notification with custom messages for different purposes

        Args:
            slack_msg: The custom message being sent.
    """

    slack_url = "https://hooks.slack.com/services/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"

    payload = {"text": slack_msg}

    try:
        r = requests.post(slack_url, data=json.dumps(payload))
    except requests.exceptions.RequestionException as e:
        logger.info("Cairo Crawler: Error while sending controller Slack notification")
        logger.info(e)

def request_API(origin, destination, mode):
    """
    Uses Google Distance Matrix AP
    matrix of origins and destinations.

    Args:
        origin: Coordinate of the origin
        destination: Coordinate of the destination
        mode: Mode of the travel (driving, walking, bicycling, transit). Note
              that bicycling and transit modes are not available since API
              responses will always be ZERO_RESULTS.

    Returns:
        distance: distance of this trip
        duration: duration of this trip
        duration_in_traffic: The length of time it takes to travel this route, based on current and historical traffic conditions.
    """

    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
    final_url = base_url+"origins="+origin+"&destinations="+destination+"&departure_time=now&mode="+mode+"&key="+API_key
    print(final_url)

    distance = 0
    duration = 0
    duration_in_traffic = 0

    try:
        r = requests.get(final_url)
        response = json.loads(r.content)

        if response['status'] == 'OK':
            for row in response['rows']:
                for elem in row['elements']:
                    if elem['status'] == 'OK':
                        try:
                            distance = elem['distance']['value']
                            duration = elem['duration']['value']

                            if mode == 'driving':
                                try:
                                    duration_in_traffic = elem['duration_in_traffic']['value']
                                except:
                                    slack_notification("duration_in_traffic doesn't exist.")
                        except:
                            slack_notification("Error occurred when parsing response.")

                    else:
                        slack_notification("Element status is not OK: " + elem['status'])

        else:
            print("Request status is not OK: " + response['status'])

    except requests.exceptions.RequestException as e:
        slack_notification("Cairo Crawler: Error when crawling")

    return distance, duration, duration_in_traffic

def crawl_trip(cells):
    client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
    db = client.cairo_trial

    latlongs = db.latlongs
    cursor = latlongs.find({"$or": cells})

    slack_notification("Cairo Crawler: Start Crawling Trips.")

    trip_list = []

    modes = ['walking', 'driving']
    cairo_datetime = datetime.utcnow() + timedelta(hours=2)
    cairo_date = cairo_datetime.strftime("%Y-%m-%d")
    cairo_time = cairo_datetime.strftime("%H:%M:%S")
    query_datetime = datetime.utcnow() + timedelta(hours=-5)
    query_date = query_datetime.strftime("%Y-%m-%d")
    query_time = query_datetime.strftime("%H:%M:%S")

    for idx, _ in enumerate(highway_origin):

        origin = highway_origin[idx]
        destination = highway_destination[idx]

        origin_list = origin.split(',')
        destination_list = destination.split(',')

        trip = {"coord_x": 99,
                "coord_y": 99,
                "cairo_date": cairo_date,
                "cairo_time": cairo_time,
                "query_date": query_date,
                "query_time": query_time,
                "origin_lat": origin_list[0],
                "origin_long": destination_list[1],
                "destination_lat": origin_list[0],
                "destination_long": destination_list[1]
                }

        for mode in modes:
            distance, duration, duration_in_traffic = request_API(origin, destination, mode)
            mode_distance = mode + "_distance"
            mode_duration = mode + "_duration"
            trip[mode_distance] = distance
            trip[mode_duration] = duration
            trip['driving_duration_in_traffic'] = duration_in_traffic

        trip_list.append(trip)

    for document in cursor:
        num_trips = 5
        coord = document["coord"]
        orig_latlongs = document["latlongs"][:num_trips]
        dest_latlongs = document["latlongs"][num_trips:]

        for orig_latlong, dest_latlong in zip(orig_latlongs, dest_latlongs):
            origin = str(orig_latlong[0]) + ',' + str(orig_latlong[1])
            destination = str(dest_latlong[0]) + ',' + str(dest_latlong[1])
            trip = {"coord_x": coord[0],
                    "coord_y": coord[1],
                    "cairo_date": cairo_date,
                    "cairo_time": cairo_time,
                    "query_date": query_date,
                    "query_time": query_time,
                    "origin_lat": orig_latlong[0],
                    "origin_long": orig_latlong[1],
                    "destination_lat": dest_latlong[0],
                    "destination_long": dest_latlong[1]
                    }

            for mode in modes:
                distance, duration, duration_in_traffic = request_API(origin, destination, mode)
                mode_distance = mode + "_distance"
                mode_duration = mode + "_duration"
                trip[mode_distance] = distance
                trip[mode_duration] = duration
                trip['driving_duration_in_traffic'] = duration_in_traffic

            trip_list.append(trip)

    db.crawled_trips.insert_many(trip_list)

    slack_notification("Cairo Crawler: Crawling Successful.")
