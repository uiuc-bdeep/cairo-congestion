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

def crawl_trip():

	def request_API(origin, destination, mode, departure_time):
		"""
			Uses Google Distance Matrix API to crawl travel distance and time for a matrix of origins and destinations.
		    Args:
		        origin: Coordinate of the origin
				destination: Coordinate of the destination
				mode: Mode of the travel (driving, walking, bicycling, transit). Note that bicycling and transit modes are not available since API responses will always be ZERO_RESULTS.
				departure_time: Departure time of the travel, in seconds
		    Returns:
				distance: distance of this trip
				duration: duration of this trip
		"""
		base_url = "https://maps.googleapis.com/maps/api/distancematrix/json?"
		final_url = base_url+"origins="+origin+"&destinations="+destination+"&mode="+mode+"&departure_time="+str(departure_time)+"&key="+API_key
		print(final_url)

		distance = 0
		duration = 0

		try:
			r = requests.get(final_url)
			response = json.loads(r.content)

			if response['status'] == 'OK':
				for row in response['rows']:
					for elem in row['elements']:
						if elem['status'] == 'OK':
							try:
								distance = elem['distance']['value']
								duration = elem['duration']['value']
							except:
								print("Error occurred when parsing response." )

						else:
							print("Element status is not OK: " + elem['status'])
							print(mode)

			else:
				print("Request status is not OK: " + response['status'])

		except requests.exceptions.RequestException as e:
			slack_notification("Cairo Crawler: Error when crawling")

		return distance, duration

	client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'],27017)
	db = client.cairo_trial

	record = db.latlongs
	cursor = record.find({})

	slack_notification("Cairo Crawler: Start Crawling Trips.")

	trip_list = []

	modes = ['driving', 'walking']
	current_time = int(time.time())
	time_variation_in_seconds = 60 * 60 * 2
	time_interval_in_seconds = 10 * 60
	time_two_hours = range(current_time, current_time + time_variation_in_seconds, time_interval_in_seconds)

	# origin = '0.016877118743416,31.369837007062927'
	# destination = '30.011917246091414,31.36908297493297'

	for document in cursor:
		origin = document['origin']
		destination = document['destination']

		for departure_time in time_two_hours:
			formmated_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(departure_time))
			trip = {'origin': origin, 'destination': destination, 'time': formmated_time, 'distance(driving)': 0, 'duration(driving)': 0, 'distance(walking)': 0, 'duration(walking)': 0}

			for mode in modes:
				distance, duration = request_API(origin, destination, mode, departure_time)
				trip['duration({})'.format(mode)] = duration
				trip['distance({})'.format(mode)] = distance

			trip_list.append(trip)

	db.crawled_trips.insert_many(trip_list)

	slack_notification("Cairo Crawler: Crawling Successful.")
