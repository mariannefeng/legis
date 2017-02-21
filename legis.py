from flask import Flask, request, render_template, Blueprint, jsonify, flash, redirect, url_for
from flask_socketio import SocketIO, emit
from dateutil.relativedelta import relativedelta
import datetime
import requests
import requests_cache
import random
import collections

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
    md_change.truncate()

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


@app.route('/<sunlight_id>/bill_pie_chart')
def get_bill_data(sunlight_id):
    one_year = datetime.datetime.now() + relativedelta(months=-12)
    bill_params = {'sponsor_id': sunlight_id, 'updated_since': one_year.strftime('%Y-%m-%d')}
    title_subject_data = leg.get_title_subject(bill_params)
    bill_count = collections.Counter(title_subject_data['subjects'])
    sorted_bc = bill_count.most_common(vars.MAX_BILLS_LENGTH)

    data_sum = 0
    rep_bill = {
        'id': sunlight_id,
        'sum': sum(bill_count.values()),
        'data': []
    }
    for bc in sorted_bc:
        bill_subj = {
            'bill': bc[0],
            'count': bc[1]
        }
        data_sum += bc[1]
        rep_bill['data'].append(bill_subj)
    rep_bill['dataSum'] = data_sum
    return jsonify(rep_bill)


@app.route('/thank_you')
def sources():
    with open(vars.THANK_YOU_MD, 'r') as z:
        content = z.read()
    parsed_text = content.strip()
    return render_template('md_template.html',
                           text=parsed_text,
                           title='Thank you')


@app.route('/whats_happenin')
def what_happen():
    with open(vars.WHAT_WERE_DOING_MD, 'r') as f:
        content = f.read()
    parsed_text = content.strip()
    return render_template('md_template.html',
                           text=parsed_text,
                           title='The official list of us doing things')


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
