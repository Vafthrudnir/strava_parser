from flask import Flask, render_template, request, redirect

import activity_parser
import utils

app = Flask(__name__)

# https://developers.strava.com/docs/authentication/#detailsaboutrequestingaccess
@app.route('/')
def main():
    auth_uri = utils.get_auth_uri()
    users = utils.read_saved_data()
    return render_template('main.html', auth_uri=auth_uri, users=users)


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
    saved_data = utils.read_saved_data()
    try:
        activities = utils.get_activities(saved_data[athlete_id], athlete_id)
    except KeyError:
        return 'ERROR: User not found'
    sport_data = activity_parser.parse_activities(activities)
    sum_points = sum([act['equivalent_distance'] for act in sport_data.values()])
    return render_template('activities.html', activities=sport_data.values(), athlete=saved_data[athlete_id], sum=sum_points)

