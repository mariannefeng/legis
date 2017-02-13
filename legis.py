from flask import Flask, request, jsonify, render_template
import collections
import requests
import json
import datetime
import pygal
from pygal.style import Style, CleanStyle
##test git user
app = Flask(__name__)

API_KEY = 'AIzaSyCtLpZ3MKo33ziOynkUbDJwqvF_baYY1ls'
GOOGLE_CIVIC_KEY = 'AIzaSyDny6NNitDS3FIGkXWKO8sMgsNb9-G-h6E'
OS_API_KEY= 'f8686fdf6e4871299219f398f88d508a'
OPEN_FEC_KEY = 'FiiYWSsRi01pGXUNkfhwbEX6tF84AJpJq2zp3gzq'
PRO_PUBLICA_KEY = 'oCmlfzzjf14vd9eOG16H0aLG4wJLkRxn6GX54rRS'


GOOGLE_GEOCODE_ENDPOINT = 'https://maps.googleapis.com/maps/api/geocode/json'
GOOGLE_CIVIC_ENDPOINT = 'https://www.googleapis.com/civicinfo/v2/representatives'
LEGISLATOR_ENDPOINT = 'http://openstates.org/api/v1/legislators/geo/'
BILL_ENDPOINT = 'http://openstates.org/api/v1/bills/'
COMMITTEE_ENDPOINT = 'http://openstates.org/api/v1/committees/{0}'
OPEN_FEC_ENDPOINT = 'https://api.open.fec.gov/v1'
PRO_PUBLICA_MEMBERS_ENDPOINT = 'https://api.propublica.org/congress/v1/115/{0}/members.json'
PRO_PUBLICA_MEMBER_VOTE_ENDPOINT = 'https://api.propublica.org/congress/v1/members/{0}/votes.json'
PRO_PUB_HEADERS = {'X-API-Key': PRO_PUBLICA_KEY}

def get_house_members():
    master_house_list = {}
    house_r = requests.get(PRO_PUBLICA_MEMBERS_ENDPOINT.format('house'), headers=PRO_PUB_HEADERS)
    for member in house_r.json()['results'][0]['members']:
        master_house_list['{0} {1}'.format(member['first_name'], member['last_name'])] = {}
        master_house_list['{0} {1}'.format(member['first_name'], member['last_name'])]['id'] = member['id']
        master_house_list['{0} {1}'.format(member['first_name'], member['last_name'])]['detail_url'] = member['api_uri']
    return master_house_list

def get_senate_members():
    master_senate_list = {}
    senate_r = requests.get(PRO_PUBLICA_MEMBERS_ENDPOINT.format('senate'), headers=PRO_PUB_HEADERS)
    for member in senate_r.json()['results'][0]['members']:
        master_senate_list['{0} {1}'.format(member['first_name'], member['last_name'])] = {}
        master_senate_list['{0} {1}'.format(member['first_name'], member['last_name'])]['id'] = member['id']
        master_senate_list['{0} {1}'.format(member['first_name'], member['last_name'])]['detail_url'] = member['api_uri']
    return master_senate_list

HOUSE_PROPUB = get_house_members()
SENATE_PROPUB = get_senate_members()

CURRENT_YEAR = datetime.datetime.now().year

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
                rep['name'] = civic_r.json()['officials'][index]['name']
                rep['finance'] = get_financial_data(rep['name'])
                rep['party']  = civic_r.json()['officials'][index]['party']
                rep['chamber']  = office['name']
                if rep['chamber'] == 'United States Senate':
                    # pro_pub_id = SENATE_PROPUB[rep['name']]['id']
                    member_details = SENATE_PROPUB[rep['name']]['detail_url']
                else:
                    # pro_pub_id = HOUSE_PROPUB(rep['name'])['id']
                    member_details = HOUSE_PROPUB[rep['name']]['detail_url']

                rep['committees'] = []
                country_comm_r = requests.get(member_details, headers=PRO_PUB_HEADERS)
                comms_current = []
                for comm in country_comm_r.json()['results'][0]['roles']:
                    if comm['congress'] == '115':
                        comms_current = comm['committees']
                        break

                for comm_curr in comms_current:
                    rep['committees'].append(comm_curr)

                # votes_r = requests.get(PRO_PUBLICA_MEMBER_VOTE_ENDPOINT.format(pro_pub_id), params=PRO_PUB_PARAMS)

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
        print('SUNLIGHT ID', sunlight_id, rep['name'])
        bill_params = {'sponsor_id': sunlight_id, 'search_window': 'session:2017-2018'}
        subj_list = subject_list(bill_params)
        subject_count = collections.Counter(subj_list)
        pie_chart = pygal.Pie(show_legend=False, style=BILL_CHART_STYLE)
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

BILL_CHART_STYLE = Style(background='transparent',
                         plot_background='transparent',
                         transition='400ms ease-in')

FINANCE_BAR_STYLE = Style(background='transparent',
                         plot_background='transparent',
                         transition='50ms ease-in',
                          opacity='.6',
                          opacity_hover='.9',
                          title_font_size=20)

def get_financial_data(names):
    if CURRENT_YEAR % 2 == 0:
        election_year = CURRENT_YEAR
    else:
        election_year = CURRENT_YEAR - 1
    committee_search_filter = {'q': names,
                              'cycle' : election_year,
                              'api_key': OPEN_FEC_KEY}
    committees_r = requests.get(OPEN_FEC_ENDPOINT + '/candidates/search/', params=committee_search_filter)
    candidate_committees = []
    for result in committees_r.json()['results']:
        cand_comm = {}
        cand_comm['candidate'] = result['name']
        cand_comm['committee_id'] = result['principal_committees'][0]['committee_id']
        candidate_committees.append(cand_comm)

    # contrib_pie = pygal.Pie(show_legend=False, style=LEGIS_STYLE, half_pie=True)
    contrib_pie = pygal.HorizontalBar(show_legend=False, style=FINANCE_BAR_STYLE)
    contrib_pie.title = '% Total Contributions By Size'

    for cand in candidate_committees:
        print(cand['candidate'])
        commitee_id = cand['committee_id']
        contrib_params = {'api_key' : OPEN_FEC_KEY,
                          'cycle' : election_year,
                          'sort' : 'size'}
        contrib_r = requests.get(OPEN_FEC_ENDPOINT + '/committee/{0}/schedules/schedule_a/by_size/'.format(commitee_id), params=contrib_params)
        print(contrib_r.json()['results'])
        for i, contrib in enumerate(contrib_r.json()['results']):
            if i == 0:
                contrib_pie.add(str(contrib['size']) + '-' + str(contrib_r.json()['results'][i + 1]['size']), contrib['total'])
            elif i == len(contrib_r.json()['results']) - 1:
                contrib_pie.add(str(contrib['size']) + '+', contrib['total'])
            else:
                contrib_pie.add(str(contrib['size']) + '-' + str(contrib_r.json()['results'][i + 1]['size']), contrib['total'])

    return contrib_pie.render_data_uri()


SOCIAL_ENDPOINTS = {
    'Facebook' : 'https://www.facebook/com/',
    'Twitter' : 'https://twitter.com/',
    'YouTube' : 'https://www.youtube.com/user/',
    'GooglePlus' : 'https://plus.google.com/'
}


if __name__ == '__main__':
    app.run()
