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


running = 1

client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
db = client.cairo_trial

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

def crawl():
    global cells
    crawl_trip(cells)
    print("Crallw")
    return schedule.CancelJob

def write_csv():
    make_csv()
    return schedule.CancelJob

def schedule_trips():
    global running
    running = 1

    timestamps = ["04:00", "04:20", "04:40", "05:00", "05:20", "05:40", "06:00",
                  "06:20", "06:40", "07:00", "07:20", "07:40", "08:00", "08:20",
                  "08:40", "09:00", "09:20", "09:40", "10:00", "10:20", "10:40",
                  "11:00", "11:20", "11:40", "12:00", "12:20", "12:40", "13:00",
                  "13:20", "13:40", "14:00"]

    # Schedule Monday trips
    for timestamp in timestamps:
        schedule.every().monday.at(timestamp).do(crawl)
    # Schedule Tuesday trips
    for timestamp in timestamps:
        schedule.every().tuesday.at(timestamp).do(crawl)
    # Schedule Wednesday trips
    for timestamp in timestamps:
        schedule.every().wednesday.at(timestamp).do(crawl)
    # Schedule Thursday trips
    for timestamp in timestamps:
        schedule.every().thursday.at(timestamp).do(crawl)
    # Schedule Friday trips
    for timestamp in timestamps:
        schedule.every().friday.at(timestamp).do(crawl)

    slack_msg = "Cairo Crawler: Scheduled Crawling Trips"
    slack_notification(slack_msg)


def end_scheduler():
    global running
    running = 0
    return schedule.CancelJob

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


def main():
    slack_msg = "Cairo Crawler: Initiating Controller"
    slack_notification(slack_msg)

    db.latlongs.drop()
    db.crawled_trips.drop()

    load_latlongs()

    while True:
        # Schedule crawls every Sunday-Thursday on 11:00PM
        schedule_trips()

        # # Schedule CSV file creation every Monday-Friday
        schedule.every().monday.at("15:00").do(write_csv)
        schedule.every().tuesday.at("15:00").do(write_csv)
        schedule.every().wednesday.at("15:00").do(write_csv)
        schedule.every().thursday.at("15:00").do(write_csv)
        schedule.every().friday.at("15:00").do(write_csv)
        schedule.every().friday.at("16:00").do(end_scheduler)

        while True and running:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    main()
