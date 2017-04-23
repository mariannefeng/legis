import collections
import datetime
import sys
import os
import json

import requests_cache
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify
from flask_restful import reqparse

import legis_data.process.VARS as vars
import legis_data.process.legwork as leg

app = Flask(__name__)
app.secret_key = 'super secret key'

# cache for requests
requests_cache.install_cache('test_cache', backend='sqlite', expire_after=300)

address_parser = reqparse.RequestParser()
address_parser.add_argument("google_address", required=True, help="google_address param required!")

time_parser = reqparse.RequestParser()
time_parser.add_argument("yearmonthdate", required=False)

state_bill_parser = reqparse.RequestParser()
state_bill_parser.add_argument("keyword", required=False)

"""
Lotsa shit to do regarding this.
There aren't many endpoints, We should probably make one for individual legislators so we can give
people the option to get more info etc
Also should be the ability to filter with query parameters when grabbing legislation. Ideally we wouldn't process
data the request doesn't want
"""


@app.route('/us/map', methods=['GET'])
def get_topojson_us_map(): 
    fp = os.path.dirname(os.path.realpath(__file__))
    topo_map = os.path.join(fp, 'process/misc/us-topojson.json')
    with open(topo_map) as data_file:    
        data = json.load(data_file)
    
    return jsonify(data)

# # federal level
@app.route('/us/senators/all', methods=['GET'])
def get_senate_members():
    return jsonify(leg.SENATE_PROPUB)


@app.route('/us/house/all', methods=['GET'])
def get_house_members():
    return jsonify(leg.HOUSE_PROPUB)


@app.route('/us/my_reps', methods=['GET'])
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
    # app.logger.info('US my reps...\n{}\n\n'.format(resp))
    return jsonify(resp)


@app.route('/upcoming_house', methods=['GET'])
def upcoming_house():
    time_arg = time_parser.parse_args()['yearmonthdate']
    if time_arg is not None:
        result = leg.get_upcoming_bills(time_arg)
    else:
        # get last Monday
        today = datetime.date.today()
        today = today - datetime.timedelta(days=today.weekday())

        today = today.strftime("%Y%m%d")
        result = leg.get_upcoming_bills(today)
    return jsonify(result)


@app.route('/<state>/upcoming_bills', methods=['GET'])
def upcoming_state_bills():
    # probably call open states here if I had to guess
    return None


# state level
@app.route('/state/<sunlight_id>/common_bill_subject_data')
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


@app.route('/state/my_reps', methods=['GET'])
def get_state_reps_from_address():
    """get list of Representatives on the State level.
    Required request parameter of google_address, formatted: Address, City, State

    :return: list of State Reps
    """
    args = address_parser.parse_args()
    return jsonify(leg.create_state_leg_list(**args))


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--mock':
            from legis_data.mock_proc.mock import mock_app
            mock_app.run()
        else:
            print("The only alternate run mode available is --mock.")
            sys.exit()
    else:
        app.run(host='0.0.0.0')


if __name__ == '__main__':
    main()
