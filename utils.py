import json
import os
import time

import requests

CLIENT_ID = 65425
STRAVA_OAUTH= 'http://www.strava.com/oauth'
STRAVA_API = 'https://www.strava.com/api/v3'

if os.getenv('FLASK_ENV') == 'development':
    REDIRECT_DOMAIN = 'http://localhost:5000'
else:
    REDIRECT_DOMAIN = 'http://szabodevelopment.com'


def get_auth_uri():
    redirect_uri = f'{REDIRECT_DOMAIN}/exchange_token'
    scope = 'activity:read'
    prompt = 'force'
    auth_uri = f'{STRAVA_OAUTH}/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt={prompt}&scope={scope}'
    return auth_uri


# Renew token if it's valid only for less than 30 minutes
def token_is_valid(athlete_details):
    remaining_time = athlete_details['expires_at'] - int(time.time())
    return remaining_time > 1800


# https://developers.strava.com/docs/authentication/#refreshingexpiredaccesstokens
def refresh_token(athlete_details, athlete_id):
    return get_access_token('refresh_token', athlete_details['refresh_token'], athlete_id)


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


def read_saved_data():
    try:
        with open('save_data/tokens.json') as f:
            saved_data = json.load(f)
    except FileNotFoundError:
        saved_data = {}
    return saved_data


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



def get_activities(athlete_details, athlete_id):
    token = athlete_details['access_token']
    if not token_is_valid(athlete_details):
        token = refresh_token(athlete_details, athlete_id)
    header = {
        'Authorization': f'Bearer {token}'
    }
    resp = requests.get(f'{STRAVA_API}/activities', headers=header)
    activities = resp.json()
    # For offline testing swap the above two lines with these two:
    #with open('test_samples/activities.json') as f:
    #    activities = json.load(f)
    return activities
