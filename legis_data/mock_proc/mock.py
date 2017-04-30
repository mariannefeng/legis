"""Given a config added to the context, return custom sections of data for testing.
Essentially.. run in 'mock' mode
"""
import os
import json

from flask import Flask, request, redirect, url_for, jsonify, flash

import legis_data.process.legwork as leg

DATA_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
# load up resources
resources_file = os.path.join(DATA_PATH, 'resources.json')
with open(resources_file, 'r') as resc:
    RESOURCES = json.loads(resc.read())

mock_app = Flask(__name__)
mock_app.secret_key = 'super secret mock-ey key'


class Borg:
    __monostate = None

    def __init__(self):
        if not Borg.__monostate:
            Borg.__monostate = self.__dict__
            self.config = read_config_file()

        else:
            self.__dict__ = Borg.__monostate


def read_config_file():
    fp = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')
    with open(fp, 'r') as conf:
        config = json.loads(conf.read())
    return config


# federal level
@mock_app.route('/us/senators/all', methods=['GET'])
def get_senate_members():
    return jsonify(leg.SENATE_PROPUB)


@mock_app.route('/us/house/all', methods=['GET'])
def get_house_members():
    return jsonify(leg.HOUSE_PROPUB)

@mock_app.route('/us/<state>/reps', methods=['GET'])
def get_reps_from_state(state):
    response = jsonify([{
        "name": "Bill Nye",
        "photo": "",
        "party": "Democrat",
        "chamber": "Senate",
        "contact": {
            "url": "http://www.murray.senate.gov/public/",
            "address": "154 Russell Senate Office Building Washington, DC 20510",
            "phone": "(202) 224-2621"
        },
        "social": [
            {
                "link": "https://plus.google.com/+pattymurray",
                "type": "GooglePlus"
            },
            {
                "link": "https://twitter.com/pattymurray",
                "type": "Twitter"
            },
            {
                "link": "https://www.facebook.com/pattymurray",
                "type": "Facebook"
            },
            {
                "link": "https://www.youtube.com/user/SenatorPattyMurray",
                "type": "YouTube"
            }
        ]},
        {
            "name": "John Locke",
            "photo": "",
            "party": "Republican",
            "chamber": "Senate",
            "contact": {
                "url": "http://www.murray.senate.gov/public/",
                "address": "154 Russell Senate Office Building Washington, DC 20510",
                "phone": "(202) 224-2621"
            },
            "social": [
                {
                    "link": "https://plus.google.com/+pattymurray",
                    "type": "GooglePlus"
                },
                {
                    "link": "https://twitter.com/pattymurray",
                    "type": "Twitter"
                },
                {
                    "link": "https://www.facebook.com/pattymurray",
                    "type": "Facebook"
                },
                {
                    "link": "https://www.youtube.com/user/SenatorPattyMurray",
                    "type": "YouTube"
                }
            ]},
        {
            "representative": "rep_2",
            "position": "representative",
            "office": "1112 N 1st Dr"
        },])
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@mock_app.route('/us/my_reps', methods=['GET'])
def get_us_reps_from_address():
    """get a list of United States Representatives and Senators at the federal level.
    Required request parameter of google_address, formatted: Address, City, State

    If there are errors, there will only be one map in the list, formatted as such:
    [
        {"error" : {"<error_type>": "<error_message"}}
    ]
    :return: list of US reps
    """
    us_reps = Borg().config.get('us')
    if us_reps:
        us_rep_file = os.path.join(DATA_PATH, 'us_rep.json')
        with open(us_rep_file, 'r') as us:
            us_rep = json.load(us)
        reps = get_reps_from_config_section(us_rep, us_reps, leg.USLegislator)
    else:
        reps = []
    return jsonify(reps)


def get_reps_from_config_section(base_config, borg_config, class_type):
    reps = []
    for rep_config in borg_config:
        rep = class_type(**base_config)
        # this is specific stuff that isn't just true/false
        # committees
        set_mock_committees(rep_config, rep)
        # bill charts specific stuff
        rep.bill_chart_type = rep_config.get('bill_chart_type', None)
        if rep.bill_chart_type == 'word_cloud':
            rep.bill_chart_data = RESOURCES.get('bill_chart_data')
        # finally can iterate through the config because the rest is just
        # booleans about whether or not to include the data.
        for field, include in rep_config.items():
            if include is True:
                rep.__dict__[field] = RESOURCES.get(field)
                print("SET FIELD {0} TO {1}".format(field, RESOURCES.get(field)))
                print(rep.__dict__[field])
        reps.append(rep.__dict__)
    return reps


def set_mock_committees(legislator_config, legislator):
    if legislator_config.get('committees'):
        committee_len = legislator_config.get('committees')
        mock_committees = RESOURCES.get('committees')
        if committee_len > len(mock_committees):
            legislator.committees = mock_committees
        else:
            legislator.committees = mock_committees[:len(mock_committees)]


# state level
@mock_app.route('/state/<sunlight_id>/common_bill_subject_data')
def get_bill_data(sunlight_id):
    print("HITTING PIE DATA")
    pie_data = os.path.join(DATA_PATH, 'pie.json')
    with open(pie_data, 'r') as data:
        rep_bill = json.loads(data.read())
    response = jsonify(rep_bill)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@mock_app.route('/state/my_reps', methods=['GET'])
def get_state_reps_from_address():
    """get list of Representatives on the State level.
    Required request parameter of google_address, formatted: Address, City, State

    :return: list of State Reps
    """
    state_reps = Borg().config.get('state')
    if state_reps:
        state_rep_file = os.path.join(DATA_PATH, 'state_rep.json')
        with open(state_rep_file, 'r') as state:
            state_rep = json.load(state)
        reps = get_reps_from_config_section(state_rep, state_reps, leg.StateLegislator)
    else:
        reps = []
    return jsonify(reps)


# sketchity sketch uploads lol
@mock_app.route('/config_upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        current = Borg()
        try:
            current.config = json.loads(file.stream.getvalue().decode())
        except:
            return '''
                    <!doctype html>
                    <title>Error parsing json config file. Try Again </title>
                    <h1>Upload new File</h1>
                    <form method=post enctype=multipart/form-data>
                      <p><input type=file name=file>
                         <input type=submit value=Upload>
                    </form>
                    '''
        # if file and file.filename[-4:] == 'json':
        #     file.save(os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__))), 'config.json'))
        return redirect(url_for('current_config'))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


@mock_app.route('/current_config', methods=['GET'])
def current_config():
    # this is super djanky
    return jsonify(Borg().config)
