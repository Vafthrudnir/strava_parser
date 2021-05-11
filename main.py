import os

from flask import Flask, render_template, request, redirect, abort

import activity_parser
import utils

app = Flask(__name__)

# https://developers.strava.com/docs/authentication/#detailsaboutrequestingaccess
@app.route('/')
def main():
    auth_uri = utils.get_auth_uri()
    users = utils.read_saved_tokens()
    teams = utils.load_teams()
    timestamp = utils.get_last_update()
    return render_template('main.html', auth_uri=auth_uri, users=users, teams=teams, last_update=timestamp)


# https://developers.strava.com/docs/authentication/#tokenexchange
@app.route('/exchange_token')
def exchange_token():
    code = request.args.get('code')
    scope = request.args.get('scope')
    if scope != 'read,activity:read':
        return 'ERROR: Authorization to reading activities is strictly required to participate!'
    utils.get_access_token('authorization_code', code)
    # Token saved, load main page
    return redirect("/", code=302)


# https://www.strava.com/api/v3/activities -H 'Authorization: Bearer YOURACCESSTOKEN'
@app.route('/athlete')
def get_user_data():
    athlete_id = request.args.get('id')
    if not athlete_id:
        return 'ERROR: Athlete ID is required for this operation'
    saved_data = utils.read_saved_tokens()
    try:
        activities = utils.get_activities(saved_data[athlete_id], athlete_id)
    except KeyError:
        return 'ERROR: User not found.\n<a href="/">Back to home page</a> '
    sport_data = activity_parser.parse_activities(activities)
    sum_points = activity_parser.sum_points(sport_data)
    utils.update_scores(sum_points, athlete_id)
    return render_template('activities.html', activities=sport_data.values(), athlete=saved_data[athlete_id], sum=sum_points)


@app.route('/refresh_teams_data')
def refresh_teams_data():
    # Password protection to avoid reaching the Strava API call limit too easily
    password = request.args.get('pw')
    if password != os.getenv('REFRESH_PASSWORD'):
        return abort(404)
    utils.update_teams_data()
    # Team data updated, return to main page
    return redirect("/", code=302)
