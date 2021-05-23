import json
import os
import time
import html

import requests

import activity_parser

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
    # Use API only if not in dev mode
    if os.getenv('FLASK_ENV') != 'development':
        resp = requests.post(url=f'{STRAVA_OAUTH}/token', data=token_exchange_data)
        token_data = resp.json()
    else:
        with open('test_samples/token_exchange.json') as f:
            token_data = json.load(f)
    if athlete:
        save_access_data(token_data, athlete)
    else:
        save_access_data(token_data)
    return token_data['access_token']


def read_saved_tokens():
    try:
        with open('save_data/tokens.json') as f:
            saved_data = json.load(f)
    except FileNotFoundError:
        saved_data = {}
    return saved_data


# 'token_data' is in json dictionary format returned by the strava token exchange
def save_access_data(token_data, athlete_id=None):
    # Saved data format: {athlete_id: {"expires_at": X, "refresh_token": "XXX", "access_token": "YYY", "firstname": "ZZZ", "lastname:" "AAA"}}
    saved_data = read_saved_tokens()
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

class API_Error(Exception):
    pass


def get_activities(athlete_details, athlete_id):
    token = athlete_details['access_token']
    if not token_is_valid(athlete_details):
        token = refresh_token(athlete_details, athlete_id)
    header = {
        'Authorization': f'Bearer {token}'
    }
    # Use API only if not in dev mode
    if os.getenv('FLASK_ENV') != 'development':
        page = 1
        activities = []
        while True:
            resp = requests.get(f'{STRAVA_API}/activities?after={activity_parser.START_EPOCH}&page={page}&per_page=100', headers=header)
            if resp.status_code != 200:
                raise API_Error(f'Status code: {resp.status_code}')
            if resp.content == b'[]':
                break
            activities_on_this_page = resp.json()
            activities += activities_on_this_page
            # We request 100 per page, but the API docs say that it's possible it returns fewer than that.
            # Let's assume though we won't get less than half for it.
            # This needs to be done to limit the number of API accesses - +1 access for each user is too much.
            if len(activities_on_this_page) < 50:
                break
            page = page + 1
    else:
        with open('test_samples/activities.json') as f:
            activities = json.load(f)
    return activities[::-1]


def read_teams_data():
    with open('save_data/teams.json') as f:
        saved_data = json.load(f)
    return saved_data


def update_teams_data():
    teams = read_teams_data()
    token_data = read_saved_tokens()
    for team, members in teams.items():
        for member in members:
            try:
                activities = get_activities(token_data[member], member)
            except KeyError:
                teams[team][member] = ''
                continue
            except API_Error as err:
                raise err
            details = activity_parser.parse_activities(activities)
            summed = activity_parser.sum_points(details)
            teams[team][member] = str(summed)
    with open('save_data/teams.json', 'w') as f:
        f.write(json.dumps(teams))
    last_updated = str(int(time.time()))
    with open('save_data/last_updated.stamp', 'w') as f:
        f.write(last_updated)


def load_teams():
    teams = read_teams_data()
    sorted_teams = []
    for team, members in teams.items():
        points = sum([int(dist) if dist else 0 for dist in members.values()])
        sorted_teams.append((html.unescape(team), members, points))
    sorted_teams = sorted(sorted_teams, key=lambda item: item[2], reverse=True)
    return sorted_teams


def get_last_update():
    try:
        with open('save_data/last_updated.stamp') as f:
            last_update = int(f.read())
    except FileNotFoundError:
        last_update = 0
    current_time = int(time.time())
    diff = current_time - last_update
    days = diff // (60 * 60 * 24)
    if days:
        return 'More than a day ago'
    hours = diff // (60 * 60)
    if hours:
        return f'{hours} hour(s) ago'
    minutes = diff // 60
    if minutes:
        return f'{minutes} minute(s) ago'
    return 'Just now'


def update_scores(sum_points, athlete_id):
    teams = read_teams_data()
    for team in teams:
        if athlete_id in teams[team]:
            teams[team][athlete_id] = str(sum_points)
            with open('save_data/teams.json', 'w') as f:
                f.write(json.dumps(teams))
            break
    return
