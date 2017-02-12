from flask import Flask, request, jsonify, render_template
import collections
import requests
import json
import pygal
from pygal.style import Style

app = Flask(__name__)

API_KEY = 'AIzaSyCtLpZ3MKo33ziOynkUbDJwqvF_baYY1ls'
GOOGLE_CIVIC_KEY = 'AIzaSyDny6NNitDS3FIGkXWKO8sMgsNb9-G-h6E'
OS_API_KEY= 'f8686fdf6e4871299219f398f88d508a'

GOOGLE_GEOCODE_ENDPOINT = 'https://maps.googleapis.com/maps/api/geocode/json'
GOOGLE_CIVIC_ENDPOINT = 'https://www.googleapis.com/civicinfo/v2/representatives'
LEGISLATOR_ENDPOINT = 'http://openstates.org/api/v1/legislators/geo/'
BILL_ENDPOINT = 'http://openstates.org/api/v1/bills/'
COMMITTEE_ENDPOINT = 'http://openstates.org/api/v1/committees/{0}'

SOCIAL_ENDPOINTS = {
    'Facebook' : 'https://www.facebook/com/',
    'Twitter' : 'https://twitter.com/',
    'YouTube' : 'https://www.youtube.com/user/',
    'GooglePlus' : 'https://plus.google.com/'
}

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
                rep = {}
                print(office)
                rep['name'] = civic_r.json()['officials'][index]['name']
                rep['party']  = civic_r.json()['officials'][index]['party']
                rep['chamber']  = office['name']
                rep['photo'] = civic_r.json()['officials'][index].get('photoUrl')
                rep['contact'] = {}
                rep['contact']['phone'] = civic_r.json()['officials'][index].get('phones')[0]
                address_map = civic_r.json()['officials'][index].get('address')[0]
                rep['contact']['address'] = '{0} {1}, {2} {3}'.format(address_map['line1'], address_map['city'],
                                                                      address_map['state'], address_map['zip'])
                rep['contact']['url'] = civic_r.json()['officials'][index].get('urls')[0]

                rep['social'] = []
                for social in civic_r.json()['officials'][index].get('channels'):
                    rep_social = {}
                    type = social['type']
                    rep_social['type'] = type
                    rep_social['link'] = SOCIAL_ENDPOINTS[type] + social['id']
                    print(rep['social'])
                    rep['social'].append(rep_social)
                my_reps.append(rep)

    r = requests.get(GOOGLE_GEOCODE_ENDPOINT, params=payload)
    # print(json.dumps(r.json()['results'][0]))
    location_obj = r.json()['results'][0]['geometry']['location']
    sunlight_payload = {'lat': location_obj.get('lat'), 'long': location_obj.get('lng')}
    r = requests.get(LEGISLATOR_ENDPOINT, params=sunlight_payload)
    legislators_info = r.json()
    for legislator in legislators_info:
        rep = {}
        rep['name'] = legislator.get('full_name')
        rep['party'] = legislator.get('party')
        rep['photo'] = legislator.get('photo_url')
        rep['chamber'] = 'House' if legislator.get('chamber') == 'lower' else 'Senate'
        # MULTIPLE OFFICES? right now just taking the first in array
        rep['contact'] = legislator.get('offices')[0]
        rep['contact']['url'] = legislator.get('url')
        rep['contact'].pop('fax')
        rep['contact'].pop('name')
        rep['contact'].pop('type')
        #  get committee info
        rep['committees'] = []
        for role in legislator.get('roles'):
            if role.get('committee_id'):
                committee = {'position': role.get('position').title(), 'name': role.get('committee')}
                rep['committees'].append(committee)
        # # pull legislator id for bill info
        sunlight_id = legislator.get('id')
        # get billz
        # rep['bills'] = []
        bill_params = {'sponsor_id': sunlight_id, 'search_window': 'session:2017-2018'}
        subj_list = subject_list(bill_params)
        subject_count = collections.Counter(subj_list)
        pie_chart = pygal.Pie(show_legend=False, style=LEGIS_STYLE)
        pie_chart.title = 'Bills Speak Louder than Words'
        for subject, count in subject_count.items():
            pie_chart.add(subject, count)
        rep['chart'] = pie_chart.render_data_uri()
        # bill_r = requests.get(BILL_ENDPOINT, params=bill_params)
        # for sunlight_bill in bill_r.json():
        #     bill = {}
        #     bill['title'] = sunlight_bill['title']
        #     bill['type'] = sunlight_bill['type']
        #     bill['subjects'] = sunlight_bill['subjects']
        #     bill['official_id'] = sunlight_bill['bill_id']
        #     # details = requests.get(BILL_ENDPOINT+sunlight_bill['id']).json()
        #     # bill['sources'] = details['sources']
        #     # bill['passed_upper'] = details['action_dates'].get('passed_upper')
        #     # bill['passed_lower'] = details['action_dates'].get('passed_lower')
        #     # bill['signed'] = details['action_dates'].get('signed')
        #     rep['bills'].append(bill)
        my_reps.append(rep)
    return render_template('reps.html', reps=my_reps)



def subject_list(bill_params):
    bill_r = requests.get(BILL_ENDPOINT, params=bill_params)
    subjects = []
    for sunlight_bill in bill_r.json():
        if sunlight_bill['subjects']:
            subjects += sunlight_bill['subjects']
        else:
            subjects.append('None')
    return subjects

LEGIS_STYLE = Style(background='transparent',
                    plot_background='transparent',
                    transition='400ms ease-in')



if __name__ == '__main__':
    app.run()
