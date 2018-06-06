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

def make_csv():
    """
        Pulls trips from the database, and output to a CSV file.
    """

    csv_path = "/data/cairo-congestion.csv"

    client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
    db = client.cairo_trial
    crawled_trips = db.crawled_trips
    cursor = list(crawled_trips.find({}))

    slack_notification("Cairo Crawler: Writing CSV file.")

    with open(csv_path, 'w') as csv_file:
        fieldnames = ["coord", "cairo_time", "query_time", "origin_latlong",
                       "destination_latlong", "driving_distance", "driving_duration",
                       "walking_distance", "walking_duration"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for doc in cursor:
            writer.writerow({"coord": doc["coord"],
                             "cairo_time": doc["cairo_time"],
                             "query_time": doc["query_time"],
                             "origin_latlong": doc["origin_latlong"],
                             "destination_latlong": doc["destination_latlong"],
                             "driving_distance": doc["driving_distance"],
                             "driving_duration": doc["driving_duration"],
                             "walking_distance": doc["walking_distance"],
                             "walking_duration": doc["walking_duration"]
                             })
    csv_file.close()

    slack_notification("Cairo Crawler: CSV file was successfully written to the shared disk.")
