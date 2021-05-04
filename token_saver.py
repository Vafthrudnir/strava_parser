import json
import os
import requests
import time

from flask import Flask
from flask import render_template
from flask import request

app = Flask(__name__)

CLIENT_ID = 65425
STRAVA_OUATH= 'http://www.strava.com/oauth'
STRAVA_API = 'https://www.strava.com/api/v3/'

# https://developers.strava.com/docs/authentication/#detailsaboutrequestingaccess
@app.route('/')
def main():
    auth_uri = get_auth_uri()
    users = read_saved_data()
    print(users)
    return render_template('main.html', auth_uri=auth_uri, users=users)

def get_auth_uri():
    redirect_uri = 'http://localhost:5000/exchange_token'
    scope = 'activity:read'
    prompt = 'force'
    auth_uri = f'{STRAVA_OUATH}/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt={prompt}&scope={scope}'
    return auth_uri


def read_saved_data():
    try:
        with open('saved_tokens.json') as f:
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
    token_exchange_data = {
        'client_id': CLIENT_ID,
        'code': code,
        'grant_type': 'authorization_code',
        'client_secret': os.environ['CLIENT_SECRET']
    }
    # TODO: enable these two lines for live function:
    #resp = requests.post(url=f'{STRAVA_OAUTH}/token', data=token_exchange_data)
    #token_data = resp.json()
    # TODO: And remove these two:
    with open('test_samples/token_exchange.json') as f:
        token_data = json.load(f)
    save_access_data(token_data)
    return 'token saved'

# 'token_data' is in json dictionary format returned by the strava token exchange
def save_access_data(token_data):
    # Saved data format: {athlete_id: {"expires_at": X, "refresh_token": "XXX", "access_token": "YYY", "firstname": "ZZZ", "lastname:" "AAA"}}
    saved_data = read_saved_data()
    athlete_id = str(token_data['athlete']['id'])
    saved_data[athlete_id] = {
        'expires_at': token_data['expires_at'],
        'access_token': token_data['access_token'],
        'refresh_token': token_data['refresh_token'],
        'firstname': token_data['athlete']['firstname'],
        'lastname': token_data['athlete']['lastname'],
    }
    with open('saved_tokens.json', 'w') as f:
        f.write(json.dumps(saved_data))


@app.route('/athlete')
def get_user_data():
#https://www.strava.com/api/v3/activities -H 'Authorization: Bearer d1ccbe9e0ff92b848dd61d1ffe9f7c636b8c0ad2'
    #requests.get()
    saved_data = read_saved_data()
    return 'hah'