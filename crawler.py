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

# def logging_init():
#     """Initiates the logger
#     Initiates the logger, the logger handler (for file handling), and the
#     formatter
#     """
#
#     logger = logging.getLogger("cairo_crawler")
#     logger.setLevel(logging.INFO)
#
#     log_handler = logging.FileHandler("cairo_crawler.log", mode="w")
#
#     formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#     log_handler.setFormatter(formatter)
#     logger.addHandler(lh)
#
#     return logger, log_handler

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

def crawl_trip(num_latlongs):
	"""
		Description.
	"""

	def request_API(latlong_o, latlong_d, mode, departure_time):
		base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
		final_url = base_url+"origins="+latlong_o+"&destinations="+latlong_d+"&mode="+mode+"&departure_time="+str(departure_time)+"&key="+API_key
		formmated_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(departure_time))
		print(final_url)

		try:
			r = requests.get(final_url)
			response = json.loads(r.content)
			# print(response)

			if response['status'] == 'OK':
				for row in response['rows']:
					for elem in row['elements']:
						if elem['status'] == 'OK':
							try:
								trip = {'origin': latlong_o, 'destination': latlong_d, 'mode': mode, 'time': formmated_time, 'distance': elem['distance']['value'], 'duration': elem['duration']['value'],
								'duration_in_traffic': elem['duration_in_traffic']['value']}
							except KeyError as e:
								trip = {'origin': latlong_o, 'destination': latlong_d, 'mode': mode, 'time': formmated_time, 'distance': elem['distance']['value'], 'duration': elem['duration']['value'],
								'duration_in_traffic': 0}
							finally:
								trip_list.append(trip)
						else:
							print("Element status is not OK: " + elem['status'])

			else:
				print("Request status is not OK: " + response['status'])

		except requests.exceptions.RequestException as e:
			slack_notification("Cairo Crawler: Error when crawling")

	client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
	db = client.cairo_trial

	record = db.latlongs
	cursor = record.find({})

	# latlongs_o = ''
	# latlongs_d = ''
	# max_docs = int(50 / num_latlongs ** 2)

	slack_notification("Cairo Crawler: Start Crawling Trips")

	trip_list = []
	# modes = ['driving', 'walking', 'bicycling', 'transit']
	# current_time = int(time.time())
	# time_variation_in_seconds = 60 * 60 * 2
	# time_interval_in_seconds = 10 * 60
	# time_two_hours = range(current_time, current_time + time_variation_in_seconds, time_interval_in_seconds)
	#
	# for document in cursor:
	# 	for idx in range(len(document['latlongs_o'])):
	# 		latlong_o = str(document['latlongs_o'][idx][0]) + ',' + str(document['latlongs_o'][idx][1])
	# 		latlong_d = str(document['latlongs_d'][idx][0]) + ',' + str(document['latlongs_d'][idx][1])
	# 		for mode in modes:
	# 			for departure_time in time_two_hours:
	# 				request_API(latlong_o, latlong_d, mode, str(departure_time))
	# db.crawled_trips.insert_many(trip_list)

		# for latlong in document['latlongs_o']:
		# 	if latlongs_o == '' :
		# 		latlongs_o += str(latlong[0]) + ',' + str(latlong[1])
		# 	else:
		# 		latlongs_o += '|' + str(latlong[0]) + ',' + str(latlong[1])
		# for latlong in document['latlongs_d']:
		# 	if latlongs_d == '' :
		# 		latlongs_d += str(latlong[0]) + ',' + str(latlong[1])
		# 	else:
		# 		latlongs_d += '|' + str(latlong[0]) + ',' + str(latlong[1])
		# time.sleep(1)

	# latlongs_o = '0.016877118743416,31.369837007062927|30.017021077370128,31.37504143475955'
	# latlongs_d = '30.011917246091414,31.36908297493297|30.018204194261003,31.366151940799767'
	latlongs_o = '0.016877118743416,31.369837007062927'
	latlongs_d = '30.011917246091414,31.36908297493297'

	modes = ['driving', 'walking', 'bicycling', 'transit']
	current_time = int(time.time())
	time_variation_in_seconds = 60 * 60 * 2
	time_interval_in_seconds = 10 * 60
	time_two_hours = range(current_time, current_time + time_variation_in_seconds, time_interval_in_seconds)

	for mode in modes:
		for departure_time in time_two_hours:
			request_API(latlongs_o, latlongs_d, mode, departure_time)

	# print(trip_list)
	db.crawled_trips.insert_many(trip_list)
	slack_notification("Cairo Crawler: Crawling Successful")
