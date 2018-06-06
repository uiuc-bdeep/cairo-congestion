"""
File Name: controller.py
Author: Brian Ko (swko2@illinois.edu)
Maintainer: Brian Ko (swko2@illinois.edu)
Description:
    This is the main script that controls the initiation, scheduling,
    and the operation of the Cairo crawler.
"""

import os
import logging
import json
import requests
from datetime import datetime
import time
import schedule
from latlong_generator import generate_latlongs
from crawler import crawl_trip
from csv_writer import make_csv
from pymongo import MongoClient

client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
db = client.cairo_trial

def logging_init():
    """Initiates the logger
    Initiates the logger, the logger handler (for file handling), and the
    formatter
    """

    logger = logging.getLogger("cairo_crawler")
    logger.setLevel(logging.INFO)

    log_handler = logging.FileHandler("cairo_crawler.log", mode="w")

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_handler.setFormatter(formatter)
    logger.addHandler(lh)

    return logger, log_handler

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

def load_latlongs():
    """Generates and stores the lat/longs in a database
    Calls the generate_latlongs method from latlong_generator.py and stores
    the generated data in a MongoDB database.
    """
    slack_msg = "Cairo Crawler: Generating Random Latitude/Longitudes"
    slack_notification(slack_msg)

    latlongs = generate_latlongs()
    db.latlongs.insert_many(latlongs)

    slack_msg = "Cairo Crawler: Inserted Random Latitude/Longitudes into MongoDB"
    slack_notification(slack_msg)

slack_msg = "Cairo Crawler: Initiating Controller"
slack_notification(slack_msg)

def main():
    db.latlongs.drop()
    db.crawled_trips.drop()

    load_latlongs()
    cells = [{"coord": [17,8]},
             {"coord": [17,9]},
             {"coord": [17,10]},
             {"coord": [17,11]},
             {"coord": [18,8]},
             {"coord": [18,9]},
             {"coord": [18,10]},
             {"coord": [18,11]},
             {"coord": [19,8]},
             {"coord": [19,9]},
             {"coord": [19,10]},
             {"coord": [19,11]},
             {"coord": [20,8]},
             {"coord": [20,9]},
             {"coord": [20,10]},
             {"coord": [20,11]}]

    start_day = "Tuesday"
    start_hour = "23"
    start_min = "00"
    end_day = "Wednesday"
    end_hour = "04"
    end_min = "00"

    while True:
        current_time = datetime.now()
        if start_day == now.strftime("%A") and start_hour == str(now.hour) and start_min == str(now.minute):
            schedule.every(20).minutes.do(crawl_trips, cells).tag("crawler")
            schedule.run_pending()
        if end_day == now.strftime("%A") and end_hour == str(now.hour) and end_min == str(now.minute):
            schedule.clear("crawler")
            break
        time.sleep(1)

    make_csv()


if __name__ == "__main__":
    main()
