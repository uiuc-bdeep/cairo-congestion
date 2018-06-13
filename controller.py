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
cells = [{"coord": [4,5]}, # 6th of October City
         {"coord": [4,6]}, # 6th of October City
         {"coord": [6,10]}, # Sheikh Zayed City
         {"coord": [7, 10]}, # Sheikh Zayed City
         {"coord": [16,8]}, # Cairo
         {"coord": [16,9]}, # Cairo
         {"coord": [25,8]}, # New Cairo City
         {"coord": [26,9]}, # New Cairo City
         {"coord": [20,14]}, # Al Marj
         {"coord": [20,15]}, # Al Marj
         {"coord": [25,18]}, # El Obour City
         {"coord": [25,19]}, # El Obour City
         {"coord": [31,14]}, # El Shorouk City
         {"coord": [31,15]}, # El Shorouk City
         {"coord": [35,17]}, # 10th of Ramadan City
         {"coord": [36,17]}] # 10th of Ramadan City


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
    #timestamps = ["04:00", "04:20", "04:40", "05:00", "05:20", "05:40", "06:00",
    #              "06:20", "06:40", "07:00", "07:20", "07:40", "08:00", "08:20",
    #              "08:40", "09:00", "09:20", "09:40", "10:00", "10:20", "10:40",
    #              "11:00", "11:20", "11:40", "12:00", "12:20", "12:40", "13:00",
    #              "13:20", "13:40", "14:00"]

    # Crawl data at Cairo time from 7am to 4pm
    timestamps = ["05:00", "05:20", "05:40", "06:00",
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
        schedule.every().monday.at("15:00").do(write_csv)
        schedule.every().tuesday.at("15:00").do(write_csv)
        schedule.every().wednesday.at("15:00").do(write_csv)
        schedule.every().thursday.at("15:00").do(write_csv)
        schedule.every().friday.at("15:00").do(write_csv)
        schedule.every().friday.at("16:00").do(end_scheduler)

        # Continuously run pending jobs
        while True and running:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    main()
