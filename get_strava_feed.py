import requests
import json
import argparse
from bs4 import BeautifulSoup


STRAVA_URL = 'https://www.strava.com/athletes'


def get_raw_data(athlete_id):
	html_text = requests.get(f'{STRAVA_URL}/{athlete_id}').text
	soup = BeautifulSoup(html_text, 'html.parser')
	mydiv = soup.find("div", {"data-react-class": "AthleteProfileApp"})
	return mydiv['data-react-props']


def parse_recent_activities(raw_data):
	activity_dict = {}
	for activity in json.loads(raw_data)['recentActivities']:
		sport = activity['type']
		# TODO: types needs to be checked, ride & run is certain, others are untested yet
		if sport not in ['ride', 'run', 'walk', 'hike', 'swim']:
			continue
		# TODO: distance is truncated to .1 km
		id, distance = activity['id'], float(activity['distance'].split(' ')[0])
		activity_dict[id] = (sport, distance)
	return activity_dict


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('athlete', help='ID of athlete')
	args = parser.parse_args()
	
	raw_data = get_raw_data(args.athlete)
	activities = parse_recent_activities(raw_data)
	print(activities)
