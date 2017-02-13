from flask import Flask, request, jsonify, render_template, Blueprint
import requests
import requests_cache
import os

import datetime
import pygal
from pygal.style import Style
##test git user

import legis_legwork as leg
import VARS as vars


app = Flask(__name__)
# create additional static directory
blueprint = Blueprint('clouds', __name__, static_url_path='/clouds', static_folder='clouds/')
app.register_blueprint(blueprint)

# cache for requests
requests_cache.install_cache('test_cache', backend='sqlite', expire_after=300)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/my_reps', methods=['POST'])
def return_data():
    my_reps = []
    # print(list(request.form.values()))
    # need validations on form
    googled_string = ', '.join(list(request.form.values()))

    payload = {'address': googled_string, 'key': vars.API_KEY}
    civic_payload = {'address': googled_string, 'key': vars.GOOGLE_CIVIC_KEY, 'levels': 'country'}

    civic_r = requests.get(vars.GOOGLE_CIVIC_ENDPOINT, params=civic_payload)

    for office in civic_r.json()['offices']:
        if office['divisionId'] != "ocd-division/country:us":
            for index in office['officialIndices']:
                rep = leg.map_json_to_us_leg(civic_r.json()['officials'][index], office['name'])
                my_reps.append(rep)

    r = requests.get(vars.GOOGLE_GEOCODE_ENDPOINT, params=payload)
    location_obj = r.json()['results'][0]['geometry']['location']

    sunlight_payload = {'lat': location_obj.get('lat'), 'long': location_obj.get('lng')}
    r = requests.get(vars.LEGISLATOR_ENDPOINT, params=sunlight_payload)
    legislators_info = r.json()
    for legislator in legislators_info:
        print(legislator)
        rep = leg.map_json_to_state_leg(legislator)
        my_reps.append(rep)
    return render_template('reps.html', reps=my_reps)

SOCIAL_ENDPOINTS = {
    'Facebook' : 'https://www.facebook/com/',
    'Twitter' : 'https://twitter.com/',
    'YouTube' : 'https://www.youtube.com/user/',
    'GooglePlus' : 'https://plus.google.com/'
}


if __name__ == '__main__':
    app.run()
