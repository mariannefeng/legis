from flask import Flask, request, render_template, Blueprint, flash, redirect, url_for
from flask_socketio import SocketIO, emit
import requests
import requests_cache
import random

import legis_legwork as leg
import VARS as vars


app = Flask(__name__)
socketio = SocketIO(app)

app.secret_key = 'super secret key'
# create additional static directory
blueprint = Blueprint('clouds', __name__, static_url_path='/clouds', static_folder='clouds/')
app.register_blueprint(blueprint)

# cache for requests
requests_cache.install_cache('test_cache', backend='sqlite', expire_after=300)

@socketio.on('md change')
def md_change(data):
    md_change = open(vars.WHAT_WERE_DOING_MD, 'r+')
    md_change.write(str(data))
    md_change.close()
    emit('ACK', '')

@app.route('/')
def index():
    background_color = random.choice(vars.BULMA_COLORS)
    button_colors = [color for color in vars.BULMA_COLORS if color != background_color]
    button_color = random.choice(button_colors)
    return render_template('index.html',
                           background_color=background_color,
                           button_color=button_color)

@app.route('/whats_happenin')
def what_happen():
    with open(vars.WHAT_WERE_DOING_MD, 'r') as f:
        content = f.read()
    return render_template('what_happen.html', text=content.strip())

@app.route('/whats_happenin_edit')
def what_happen_edit():
    with open(vars.WHAT_WERE_DOING_MD, 'r') as f:
        content = f.read()
    return render_template('what_happen_edit.html', text=content.strip())

@app.route('/my_reps', methods=['POST'])
def return_data():
    errs = []
    for field, value in request.form.items():
        if not value:
           errs.append(field)
    if errs:
        if len(errs) == 1:
            flash("Field Required: {}".format(errs[0]).title())
        else:
            flash("Fields Required: {}".format(', '.join(errs)).title())
        return redirect(url_for('index'))

    human = leg.Constituent(**request.form)
    google_result = human.get_google_civic_info()

    if human.google_error:
        flash("Error from Google Civic API: {}".format(human.google_error))
        return redirect(url_for('index'))

    # Get US level legislative info
    state = google_result['normalizedInput']['state']
    for office in google_result['offices']:
        if office['divisionId'] != "ocd-division/country:us":
            for index in office['officialIndices']:
                rep = leg.map_json_to_us_leg(google_result['officials'][index], office['name'], state)
                human.representatives.append(rep)

    # Get State level legislative info
    sunlight_payload = {'lat': human.location.get('lat'), 'long': human.location.get('lng')}
    r = requests.get(vars.LEGISLATOR_ENDPOINT, params=sunlight_payload)
    legislators_info = r.json()
    for legislator in legislators_info:
        rep = leg.map_json_to_state_leg(legislator)
        human.representatives.append(rep)
    return render_template('reps.html', reps=human.representatives)


if __name__ == '__main__':
    socketio.run(app)