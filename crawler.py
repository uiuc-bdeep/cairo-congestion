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
import datetime
import logging
import time
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

def crawl_trip():
	"""
		Description.
	"""
	# Set up database connection.
	client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
	db = client.cairo_trial

	record = db.latlongs
	cursor = record.find({})

# latlongs_o': [[29.982354914326784, 31.253579544029403], [29.979453202823123, 31.250049341374503], [29.979151159470668, 31.25183382039455], [29.977454807624724, 31.253558042041572], [29.982923889889484, 31.255827854760376]], 'latlongs_d': [[29.978663178469038, 31.248589167502928], [29.981826885710493, 31.249033127260788], [29.982909663230053, 31.251046868558173], [29.980385993961043, 31.248505063413624], [29.982056992125532, 31.255021659504397]]

	# latlongs_o = ''
	# latlongs_d = ''
	latlongs_o = '29.982354914326784,31.253579544029403|29.979453202823123,31.250049341374503'
	latlongs_d = '29.978663178469038,31.248589167502928|29.981826885710493,31.249033127260788'
	count = 0

	# for document in cursor:
	# 	if count > 5:
	# 		break
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
	# 	count += 1

	slack_notification("Cairo Crawler: Start Crawling Trips")

	base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
	final_url = base_url+"origins="+latlongs_o+"&destinations="+latlongs_d+"&departure_time=now&duration_in_traffic=pessimistic&key="+API_key

	print(final_url)

	try:
		r = requests.get(final_url)
		response = json.loads(r.content)

		t_traffic = "0"
		t_dist = "0"
		t_time = "0"
		trip_list = []
		trip = {}
		print(response)

		if response["status"] == "OK":
			for row in response['rows']:
				for elem in row['elements']:
					print(elem)
					print(elem['distance']['value'])
					print("====")
					time.sleep(1)
			# for it1 in [0]['elements'][0]:
			# 	t_dist = str(response['rows'][0]['elements'][0]['distance']['value'])
			# for it2 in response['rows'][0]['elements'][0].get('duration',[]):
			# 	t_time = str(response['rows'][0]['elements'][0]['duration']['value'])
			# for it3 in response['rows'][0]['elements'][0].get('duration_in_traffic',[]):
			# 	t_traffic = str(response['rows'][0]['elements'][0]['duration_in_traffic']['value'])
		slack_notification("Cairo Crawler: Crawling Successful")

	except requests.exceptions.RequestException as e:
		slack_notification("Cairo Crawler: Error when crawling")
		t_traffic = "-1"
		t_dist = "-1"
		t_time = "-1"

	print(t_dist)
	print(t_time)
	print(t_traffic)

	db.crawled_trips.insert_many({"_id" : db_id}, {"$set": {t_type: {"distance" : t_dist , "time" : t_time , "traffic" : t_traffic }}})
	slack_notification("Cairo Crawler: Crawling Successful")
