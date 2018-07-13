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

# Global variable for scheduling
running = 1

# Initiate connection with MongoDB
client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
db = client.cairo_trial

# Specific cells that are going to be crawled
cells = [{"coord": [3,5]},
         {"coord": [3,6]},
         {"coord": [4,5]},
         {"coord": [4,6]},
         {"coord": [15,9]},
         {"coord": [15,10]},
         {"coord": [15,11]},
         {"coord": [16,9]},
         {"coord": [16,10]},
         {"coord": [16,11]},
         {"coord": [17,9]},
         {"coord": [17,10]},
         {"coord": [17,11]},
         {"coord": [18,11]},
         {"coord": [18,12]},
         {"coord": [19,11]},
         {"coord": [19,12]},
         {"coord": [20,11]},
         {"coord": [20,12]},
         {"coord": [20,13]}
         ]

def logging_init():
    """
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

def crawl():
    """
        Calls the crawling method and then cancels the scheduled trip to make
        sure that jobs aren't repeated

        Returns:
            schedule.CancelJob: Cancels the job to prevent repetition of jobs
    """

    crawl_trip(cells)
    return schedule.CancelJob

def write_csv():
    """
        Calls the csv creation method and then cancels the scheduled trip to
        make sure that jobs aren't repeated

        Returns:
            schedule.CancelJob: Cancels the job to prevent reptition of jobs
    """

    make_csv()
    db.crawled_trips.drop()
    return schedule.CancelJob

def schedule_trips():
    """
        Schedules all the crawl trips from Monday-Friday during the specified
        timestamps.
    """

    # Set running to 1 so that schedule will continuously run pending jobs
    global running
    running = 1

    # Timestamps contains all the times in which the crawling will run. All the
    # timestamps are in UTC time, which is the timezone in which the server is
    # running. The UTC timezone is two hours behind Cairo time and five hours
    # ahead of Champaign time.

    # Crawl data 24/7/365
    timestamps = ["22:00", "23:00", "00:00", "01:00", "02:00", "03:00",
                  "04:00", "05:00", "06:00", "07:00", "08:00", "09:00",
                  "10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
                  "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"]

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
    # Schedule Saturday trips
    for timestamp in timestamps:
        schedule.every().saturday.at(timestamp).do(crawl)
    # Schedule Sunday trips
    for timestamp in timestamps:
        schedule.every().sunday.at(timestamp).do(crawl)

    slack_msg = "Cairo Crawler: Scheduled Crawling Trips"
    slack_notification(slack_msg)

def end_scheduler():
    """
        Ensures that at the end of all the crawling trips and csv creation on
        Friday, the scheduler will stop.
    """

    # Set running to 0 to make sure that schedule will stop running pending jobs
    global running
    running = 0
    return schedule.CancelJob

def load_latlongs():
    """
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

    # Drops all the collections to ensure fresh data (Testing purposes)
    db.latlongs.drop()
    db.crawled_trips.drop()

    load_latlongs()

    while True:
        # Schedule crawls every Sunday-Thursday on 11:00PM
        schedule_trips()

        # Schedule CSV file creation every Monday-Friday
        schedule.every().monday.at("21:30").do(write_csv)
        schedule.every().tuesday.at("21:30").do(write_csv)
        schedule.every().wednesday.at("21:30").do(write_csv)
        schedule.every().thursday.at("21:30").do(write_csv)
        schedule.every().friday.at("21:30").do(write_csv)
        schedule.every().saturday.at("21:30").do(write_csv)
        schedule.every().sunday.at("21:30").do(write_csv)

        # Continuously run pending jobs
        while True and running:
            schedule.run_pending()
            time.sleep(0.5)

if __name__ == "__main__":
    main()
