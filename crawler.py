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
    """

    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
    final_url = base_url+"origins="+origin+"&destinations="+destination+"&mode="+mode+"&key="+API_key
    print(final_url)

    distance = 0
    duration = 0

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
                        except:
                            print("Error occurred when parsing response." )

                    else:
                        print("Element status is not OK: " + elem['status'])
                        print(mode)

        else:
            print("Request status is not OK: " + response['status'])

    except requests.exceptions.RequestException as e:
        slack_notification("Cairo Crawler: Error when crawling")

    return distance, duration

def crawl_trip(cells):
    client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
    db = client.cairo_trial

    latlongs = db.latlongs
    cursor = latlongs.find({"$or": cells})

    slack_notification("Cairo Crawler: Start Crawling Trips.")

    trip_list = []

    modes = ['driving', 'walking']
    cairo_datetime = datetime.utcnow() + timedelta(hours=2)
    cairo_date = cairo_datetime.strftime("%Y-%m-%d")
    cairo_time = cairo_datetime.strftime("%H:%M:%S")
    query_datetime = datetime.utcnow() + timedelta(hours=-5)
    query_date = query_datetime.strftime("%Y-%m-%d")
    query_time = query_datetime.strftime("%H:%M:%S")

    # origin = '30.016877118743416,31.369837007062927'
    # destination = '30.011917246091414,31.36908297493297'

    for document in cursor:
        coord = document["coord"]
        orig_latlongs = document["latlongs"][:5]
        dest_latlongs = document["latlongs"][5:]

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
                distance, duration = request_API(origin, destination, mode)
                mode_distance = mode + "_distance"
                mode_duration = mode + "_duration"
                trip[mode_distance] = distance
                trip[mode_duration] = duration

            trip_list.append(trip)
    db.crawled_trips.insert_many(trip_list)

    slack_notification("Cairo Crawler: Crawling Successful.")


            #origin_lat = document['origin'][0]
            #origin_long = document['origin'][1]
            #destination_lat = document['destination'][0]
            #destination_long = document['destination'][1]

            #origin = str(origin_lat) + ',' + str(origin_long)
            #destination = str(destination_lat) + ',' + str(destination_long)

            #for departure_time in time_two_hours:
            #        cairo_datetime = datetime.fromtimestamp(departure_time)
            #        cairo_date = cairo_datetime.strftime("%Y-%m-%d")
            #        cairo_time = cairo_datetime.strftime("%H:%M:%S")

            #        trip = {'origin_lat': origin_lat, 'origin_long': origin_long, 'destination_lat': destination_lat, 'destination_long': destination_long, 'cairo_date': cairo_date, 'cairo_time': cairo_time, 'distance(driving)': 0, 'duration(driving)': 0, 'distance(walking)': 0, 'duration(walking)': 0}

            #        for mode in modes:
            #                distance, duration = request_API(origin, destination, mode, departure_time)
            #                trip['duration({})'.format(mode)] = duration
            #                trip['distance({})'.format(mode)] = distance

            #        trip_list.append(trip)

