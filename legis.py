from flask import Flask, request, jsonify, render_template, Blueprint, flash
import requests
import requests_cache
import os
import random

import datetime
import pygal
from pygal.style import Style
##test git user

import legis_legwork as leg
import VARS as vars


app = Flask(__name__)
app.secret_key = 'super secret key'
# create additional static directory
blueprint = Blueprint('clouds', __name__, static_url_path='/clouds', static_folder='clouds/')
app.register_blueprint(blueprint)

# cache for requests
requests_cache.install_cache('test_cache', backend='sqlite', expire_after=300)

@app.route('/')
def index():
    bulma_colors = ['is-success', 'is-info', 'is-primary', 'is-warning', 'is-danger']
    background_color = random.choice(bulma_colors)
    button_colors = [color for color in bulma_colors if color != background_color]
    button_color = random.choice(button_colors)
    return render_template('index.html',
                           background_color=background_color,
                           button_color=button_color)


@app.route('/my_reps', methods=['POST'])
def return_data():
    my_reps = []
    # print(list(request.form.values()))
    # need validations on form
    errs = []
    for field, value in request.form.items():
        if not value:
           errs.append(field)
    if errs:
        if len(errs) == 1:
            flash("Field Required: {}".format(errs[0]).title())
        else:
            flash("Fields Required: {}".format(', '.join(errs)).title())
        return render_template('index.html')

    googled_string = ', '.join(list(request.form.values()))

    payload = {'address': googled_string, 'key': vars.API_KEY}
    civic_payload = {'address': googled_string, 'key': vars.GOOGLE_CIVIC_KEY, 'levels': 'country'}

    civic_r = requests.get(vars.GOOGLE_CIVIC_ENDPOINT, params=civic_payload)

    state = civic_r.json()['normalizedInput']['state']
    for office in civic_r.json()['offices']:
        if office['divisionId'] != "ocd-division/country:us":
            for index in office['officialIndices']:
                rep = leg.map_json_to_us_leg(civic_r.json()['officials'][index], office['name'], state)
                my_reps.append(rep)

    r = requests.get(vars.GOOGLE_GEOCODE_ENDPOINT, params=payload)
    location_obj = r.json()['results'][0]['geometry']['location']

    sunlight_payload = {'lat': location_obj.get('lat'), 'long': location_obj.get('lng')}
    r = requests.get(vars.LEGISLATOR_ENDPOINT, params=sunlight_payload)
    legislators_info = r.json()
    for legislator in legislators_info:
        rep = leg.map_json_to_state_leg(legislator)
        my_reps.append(rep)
    return render_template('reps.html', reps=my_reps)


if __name__ == '__main__':
    app.run()
