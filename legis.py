from flask import Flask, request, jsonify, render_template, Blueprint
import collections
import requests
import requests_cache
import json
import random
import datetime
import os
import io
import math

from dateutil.relativedelta import relativedelta
import datetime
import pygal
import nltk
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from pygal.style import Style
from PIL import Image

import legis_objektz as leg

app = Flask(__name__)
# create additional static directory
blueprint = Blueprint('clouds', __name__, static_url_path='/clouds', static_folder='clouds/')
app.register_blueprint(blueprint)

# cache for requests
requests_cache.install_cache('test_cache', backend='sqlite', expire_after=300)

API_KEY = 'AIzaSyCtLpZ3MKo33ziOynkUbDJwqvF_baYY1ls'
GOOGLE_CIVIC_KEY = 'AIzaSyDny6NNitDS3FIGkXWKO8sMgsNb9-G-h6E'
OS_API_KEY= 'f8686fdf6e4871299219f398f88d508a'
OPEN_FEC_KEY = 'FiiYWSsRi01pGXUNkfhwbEX6tF84AJpJq2zp3gzq'

GOOGLE_GEOCODE_ENDPOINT = 'https://maps.googleapis.com/maps/api/geocode/json'
GOOGLE_CIVIC_ENDPOINT = 'https://www.googleapis.com/civicinfo/v2/representatives'
LEGISLATOR_ENDPOINT = 'http://openstates.org/api/v1/legislators/geo/'
BILL_ENDPOINT = 'http://openstates.org/api/v1/bills/'
COMMITTEE_ENDPOINT = 'http://openstates.org/api/v1/committees/{0}'
OPEN_FEC_ENDPOINT = 'https://api.open.fec.gov/v1'

CURRENT_YEAR = datetime.datetime.now().year

CUSTOM_FONT = os.path.join('static', 'Helvetica-Light.ttf')

# todo - make class that represents a legislator. this shit is just getting out of hand

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/my_reps', methods=['POST'])
def return_data():
    my_reps = []
    # print(list(request.form.values()))
    # need validations on form
    googled_string = ', '.join(list(request.form.values()))

    payload = {'address': googled_string, 'key': API_KEY}
    civic_payload = {'address' : googled_string, 'key': GOOGLE_CIVIC_KEY, 'levels':'country'}

    civic_r = requests.get(GOOGLE_CIVIC_ENDPOINT, params=civic_payload)

    for office in civic_r.json()['offices']:
        if office['divisionId'] !=  "ocd-division/country:us":
            for index in office['officialIndices']:
                rep = leg.map_json_to_us_leg(civic_r.json()['officials'][index], office['name'])
                my_reps.append(rep)

    r = requests.get(GOOGLE_GEOCODE_ENDPOINT, params=payload)
    location_obj = r.json()['results'][0]['geometry']['location']

    sunlight_payload = {'lat': location_obj.get('lat'), 'long': location_obj.get('lng')}
    r = requests.get(LEGISLATOR_ENDPOINT, params=sunlight_payload)
    legislators_info = r.json()
    for legislator in legislators_info:
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
