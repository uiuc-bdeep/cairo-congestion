'''
        File Name: csv_writer.py
        Author: Zehao Chen (zehaoc2@illinois.edu)
        Maintainer: Zehao Chen (zehaoc2@illinois.edu)
        Description:
            This script pulls trips from the database, and output to a CSV file.
'''
import os
import csv
import json
import requests
import logging
import time
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps

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

def generate_id(doc, trip_num, curr_cell):
    cell = ''
    if doc["coord_x"] < 10:
        cell += '0' + str(doc["coord_x"])
    else:
        cell += str(doc["coord_x"])

    if doc["coord_y"] < 10:
        cell += '0' + str(doc["coord_y"])
    else:
        cell += str(doc["coord_y"])

    if cell != curr_cell:
        curr_cell = cell
        trip_num = 0
    else:
        trip_num += 1

    id = cell
    # Assume there're less than 100 trips per cell
    if trip_num < 10:
        id += '0' + str(trip_num)
    else:
        id += str(trip_num)
    return id, trip_num, curr_cell

def make_csv():
    """
        Pulls trips from the database, and output to a CSV file.
        Args:
            id: Identification number for each csv file we generate.
    """

    client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
    db = client.cairo_trial
    crawled_trips = db.crawled_trips
    cursor = list(crawled_trips.find({}))

    date = ''
    for doc in cursor:
        date = doc["cairo_date"]
        break

    csv_path = "/data/cairo-congestion-"+str(date)+".csv"

    slack_notification("Cairo Crawler: Writing CSV file.")

    with open(csv_path, 'w') as csv_file:
        fieldnames = ["id", "coord_x", "coord_y", "cairo_date", "cairo_time",
                      "query_date", "query_time", "origin_lat", "origin_long",
                      "destination_lat", "destination_long", "driving_distance",
                      "driving_duration", "driving_duration_in_traffic", "walking_distance", "walking_duration"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        curr_cell = ''
        trip_num = 0
        for doc in cursor:
            id, trip_num, curr_cell = generate_id(doc, trip_num, curr_cell)

            writer.writerow({"id": id,
                             "coord_x": doc["coord_x"],
                             "coord_y": doc["coord_y"],
                             "cairo_date": doc["cairo_date"],
                             "cairo_time": doc["cairo_time"],
                             "query_date": doc["query_date"],
                             "query_time": doc["query_time"],
                             "origin_lat": doc["origin_lat"],
                             "origin_long": doc["origin_long"],
                             "destination_lat": doc["destination_lat"],
                             "destination_long": doc["destination_long"],
                             "driving_distance": doc["driving_distance"],
                             "driving_duration": doc["driving_duration"],
                             "driving_duration_in_traffic": doc["driving_duration_in_traffic"],
                             "walking_distance": doc["walking_distance"],
                             "walking_duration": doc["walking_duration"]
                             })
    csv_file.close()

    slack_notification("Cairo Crawler: CSV file was successfully written to the shared disk.")
