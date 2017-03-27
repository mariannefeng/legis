"""Given a config added to the context, return custom sections of data for testing.
Essentially.. run in 'mock' mode
"""
import os
import json

from flask import Flask, request, redirect, url_for, jsonify, flash

import legis_data.process.VARS as vars
import legis_data.process.legwork as leg

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
    args = address_parser.parse_args()
    resp = leg.create_us_leg_list(**args)
    return jsonify(resp)


# state level
@mock_app.route('/state/<sunlight_id>/common_bill_subject_data')
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
    response = jsonify(rep_bill)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@mock_app.route('/state/my_reps', methods=['GET'])
def get_state_reps_from_address():
    """get list of Representatives on the State level.
    Required request parameter of google_address, formatted: Address, City, State

    :return: list of State Reps
    """
    args = address_parser.parse_args()
    return jsonify(leg.create_state_leg_list(**args))


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
    return """
    <!doctype html>
    <title>Current Config</title>
    <div>{0}</div>
    """.format(json.dumps(Borg().config))
