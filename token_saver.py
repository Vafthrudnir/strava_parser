import json
import os
import time
import re

import requests

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

app = Flask(__name__)

CLIENT_ID = 65425
STRAVA_OAUTH= 'http://www.strava.com/oauth'
STRAVA_API = 'https://www.strava.com/api/v3'

# https://developers.strava.com/docs/authentication/#detailsaboutrequestingaccess
@app.route('/')
def main():
    auth_uri = get_auth_uri()
    users = read_saved_data()
    return render_template('main.html', auth_uri=auth_uri, users=users)

def get_auth_uri():
    redirect_uri = 'http://localhost:5000/exchange_token'
    scope = 'activity:read'
    prompt = 'force'
    auth_uri = f'{STRAVA_OAUTH}/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt={prompt}&scope={scope}'
    return auth_uri


def read_saved_data():
    try:
        with open('save_data/tokens.json') as f:
            saved_data = json.load(f)
    except FileNotFoundError:
        saved_data = {}
    return saved_data


# https://developers.strava.com/docs/authentication/#tokenexchange
@app.route('/exchange_token')
def exchange_token():
    code = request.args.get('code')
    scope = request.args.get('scope')
    if scope != 'read,activity:read':
        return 'ERROR: Authorization to reading activities is strictly required to participate!'
    get_access_token('authorization_code', code)
    # Token saved, load main page
    return redirect("/", code=302)

def get_access_token(grant_type, code, athlete=None):
    token_exchange_data = {
        'client_id': CLIENT_ID,
        'client_secret': os.environ['CLIENT_SECRET'],
        'grant_type': grant_type,
        'code': code,
    }
    if grant_type == 'authorization_code':
        token_exchange_data['code'] = code
    else:
        token_exchange_data['refresh_token'] = code
    resp = requests.post(url=f'{STRAVA_OAUTH}/token', data=token_exchange_data)
    token_data = resp.json()
    # For offline testing swap the above two lines with these two:
    #with open('test_samples/token_exchange.json') as f:
    #    token_data = json.load(f)
    if athlete:
        save_access_data(token_data, athlete)
    else:
        save_access_data(token_data)
    return token_data['access_token']

# 'token_data' is in json dictionary format returned by the strava token exchange
def save_access_data(token_data, athlete_id=None):
    # Saved data format: {athlete_id: {"expires_at": X, "refresh_token": "XXX", "access_token": "YYY", "firstname": "ZZZ", "lastname:" "AAA"}}
    saved_data = read_saved_data()
    if not athlete_id:
        athlete_id = str(token_data['athlete']['id'])
    if athlete_id not in saved_data.keys(): # new entry
        saved_data[athlete_id] = {
            'firstname': token_data['athlete']['firstname'],
            'lastname': token_data['athlete']['lastname'],
        }
    saved_data[athlete_id]['expires_at'] = token_data['expires_at']
    saved_data[athlete_id]['access_token'] = token_data['access_token']
    saved_data[athlete_id]['refresh_token'] = token_data['refresh_token']
    with open('save_data/tokens.json', 'w') as f:
        f.write(json.dumps(saved_data))


# https://www.strava.com/api/v3/activities -H 'Authorization: Bearer YOURACCESSTOKEN'
@app.route('/athlete')
def get_user_data():
    athlete_id = request.args.get('id')
    if not athlete_id:
        return 'ERROR: Athlete ID is required for this operation'
    saved_data = read_saved_data()
    try:
        token = saved_data[athlete_id]['access_token']
    except KeyError:
        return 'ERROR: User not found'
    if not token_is_valid(saved_data[athlete_id]):
        token = refresh_token(saved_data[athlete_id], athlete_id)
    header = {
        'Authorization': f'Bearer {token}'
    }
    resp = requests.get(f'{STRAVA_API}/activities', headers=header)
    activities = resp.json()
    # For offline testing swap the above two lines with these two:
    #with open('test_samples/activities.json') as f:
    #    activities = json.load(f)
    sport_data = parse_activities(activities)
    sum_points = sum([act['equivalent_distance'] for act in sport_data.values()])
    return render_template('activities.html', activities=sport_data.values(), athlete=saved_data[athlete_id], sum=sum_points)

# Renew token if it's valid only for less than 30 minutes
def token_is_valid(athlete_details):
    remaining_time = athlete_details['expires_at'] - int(time.time())
    return remaining_time > 1800

# https://developers.strava.com/docs/authentication/#refreshingexpiredaccesstokens
def refresh_token(athlete_details, athlete_id):
    return get_access_token('refresh_token', athlete_details['refresh_token'], athlete_id)


# TODO: this should be organized in a separate file
ACTIVE_MONTH = '05'
allowed_sports = ['Ride', 'Walk', 'Swim', 'Hike', 'Run']
sport_weights = {
    'Ride': 1,
    'Walk': 2,
    'Hike': 2,
    'Run': 4,
    'Swim': 12,
}
def parse_activities(activities):
    summarized = {}
    for activity in activities:
        if not activity['start_date_local'].startswith(f'2021-{ACTIVE_MONTH}-'):
            continue
        if activity['type'] not in sport_weights.keys():
            continue
        details = {
            'type': activity['type'],
            'distance': activity['distance'],
            'start_date': activity['start_date_local'],
            'name': activity['name'],
            'equivalent_distance': int(activity['distance'] * sport_weights[activity['type']]),
        }
        summarized[activity['id']] = details
    return summarized
