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

def sum_points(sport_data):
	return sum([act['equivalent_distance'] for act in sport_data.values()])
