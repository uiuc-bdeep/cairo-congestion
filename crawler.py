'''
	File Name: crawler.py
	Author: Zehao Chen (zehaoc2@illinois.edu)
	Maintainer: Zehao Chen (zehaoc2@illinois.edu)
	Description:
		This script parses data from the JSON Object to form a URL and then requests data from the Google API. The response data is updated in the corresponding trip in the database.
'''

# Import libraries.
import os
import json
import requests
import logging
import time
from pprint import pprint
from pymongo import MongoClient
from bson.objectid import ObjectId

API_key = "AIzaSyADEXdHuYJDPa2K5oSzBxAUxCGEzzRvzi0"

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

def request_API(latlongs_o, latlongs_d):
	base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
	final_url = base_url+"origins="+latlongs_o+"&destinations="+latlongs_d+"&departure_time=now&key="+API_key
	print(final_url)

	try:
		r = requests.get(final_url)
		response = json.loads(r.content)

		trip_list = []
		if response["status"] == "OK":
			for row in response['rows']:
				for elem in row['elements']:
					trip = {'distance':elem['distance']['value'], 'duration':elem['duration']['value'],
					'duration_in_traffic':elem['duration_in_traffic']['value']}
					trip_list.append(trip)
		else:
			print("Over the quota.")

	except requests.exceptions.RequestException as e:
		slack_notification("Cairo Crawler: Error when crawling")

	client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
	db = client.cairo_trial
	db.crawled_trips.insert_many(trip_list)

def crawl_trip(num_latlongs):
	"""
		Description.
	"""
	client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
	db = client.cairo_trial

	record = db.latlongs
	cursor = record.find({})

	latlongs_o = ''
	latlongs_d = ''
	# max_docs = int(50 / num_latlongs ** 2)

	# slack_notification("Cairo Crawler: Start Crawling Trips")
	#
	# for document in cursor:
	# 	for latlong in document['latlongs_o']:
	# 		if latlongs_o == '' :
	# 			latlongs_o += str(latlong[0]) + ',' + str(latlong[1])
	# 		else:
	# 			latlongs_o += '|' + str(latlong[0]) + ',' + str(latlong[1])
	# 	for latlong in document['latlongs_d']:
	# 		if latlongs_d == '' :
	# 			latlongs_d += str(latlong[0]) + ',' + str(latlong[1])
	# 		else:
	# 			latlongs_d += '|' + str(latlong[0]) + ',' + str(latlong[1])
	#
	# 	request_API(latlongs_o, latlongs_d)
	# 	latlongs_o = ''
	# 	latlongs_d = ''
	# 	time.sleep(1)

# 0.016877118743416,31.369837007062927|30.017021077370128,31.37504143475955|30.01640641787756,31.371254840360127|30.012293527133682,31.37004216687616|30.010348272546235,31.373091693050185&destinations=30.011917246091414,31.36908297493297|30.018204194261003,31.366151940799767|30.01092491827021,31.36846533576398|30.013939982282253,31.375367888564387|30.01727926408631,31.369572999179546
	latlongs_o = '0.016877118743416,31.369837007062927|30.017021077370128,31.37504143475955'
	latlongs_d = '30.011917246091414,31.36908297493297|30.018204194261003,31.366151940799767'
	request_API(latlongs_o, latlongs_d)

	slack_notification("Cairo Crawler: Crawling Successful")
