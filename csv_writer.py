'''
	File Name: csv_writer.py
	Author: Zehao Chen (zehaoc2@illinois.edu)
	Maintainer: Zehao Chen(zehaoc2@illinois.edu)
	Description:
		This script pulls trips from the database, checks for errors, write trips to a JSON
		file and then output to a CSV file.
'''
# Import libraries.
import os
import csv
import json
import requests
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import dumps

def slack_notification(slack_msg):
    """Send slack notification
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
    csv_path = "/data/cairo-congestion.csv"

    client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
    db = client.cairo_trial
    cursor = list(db.crawled_trips.find({}))

    slack_notification("Cairo Crawler: Writing CSV file.")

    with open(csv_path, 'w') as csv_file:
        fieldnames = ['origin', 'destination', 'mode', 'time', 'distance', 'duration', 'duration_in_traffic']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for dict in cursor:
            writer.writerow({'origin': dict['origin'], 'destination': dict['destination'], 'mode': dict['mode'], 'time': dict['time'], 'distance': dict['distance'], 'duration': dict['duration'], 'duration_in_traffic': dict['duration_in_traffic']})

    csv_file.close()

    slack_notification("Cairo Crawler: CSV file successful wrote to shared disk.")
