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
                rep = {}
                rep['name'] = civic_r.json()['officials'][index]['name']
                # rep['finance'] = get_financial_data(rep['name'])
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
        rep['committees'] = get_committee(legislator.get('roles'))
        if not rep['committees']:
            rep['old_term_ordinal'], rep['old_committees'] = get_old_roles(legislator)
        # print('SUNLIGHT ID', sunlight_id, rep['name'])
        # # pull legislator id for bill info
        sunlight_id = legislator.get('id')
        is_word_cloud, chart = make_bill_chart(sunlight_id)
        if is_word_cloud:
            rep['wordcloud_loc'] = chart
        else:
            rep['pie_chart'] = chart
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


def turq_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    pastels = ["rgb(64,224,208)", "rgb(0,255,255)","rgb(224,255,255)", "rgb(95,158,160)"]
    return random.choice(pastels)


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "hsl(0, 0%%, %d%%)" % random.randint(60, 90)


def make_bill_chart(sunlight_id):
    one_year = datetime.datetime.now() + relativedelta(months=-12)
    bill_params = {'sponsor_id': sunlight_id, 'updated_since': one_year.strftime('%Y-%m-%d')}
    title_subject_data = subject_list(bill_params)
    subject_count = collections.Counter(title_subject_data['subjects'])
    # if 'None" comprises 50%+ of total subject data, then render a word cloud of titles instead.
    if subject_count.most_common(1)[0][0] == 'None':
        # check if it is 50%
        composition = {subject: subject_count[subject]/float(len(title_subject_data['subjects'])) for subject in subject_count}
        if composition.get('None') > .5:
            # get rid of verbs
            good_words = nltk_process(title_subject_data['titles'], 'V')
            # make word cloud
            # make circle mask
            cloud = WordCloud(font_path=CUSTOM_FONT, height=400, width=400, background_color="#ffffff").generate(' '.join(good_words))
            filename = '{}.png'.format(sunlight_id)
            cloud.recolor(color_func=grey_color_func, random_state=3).to_file(os.path.join('clouds', filename))
            return True, filename
    else:
        pie_chart = pygal.Pie(show_legend=False, style=LEGIS_STYLE, opacity_hover=.9)
        pie_chart.force_uri_protocol = 'http'
        pie_chart.title = 'Bills Speak Louder than Words'
        for subject, count in subject_count.items():
            pie_chart.add(subject, count)
        return False, pie_chart.render_data_uri()


def get_committee(role_array):
    committees = []
    for role in role_array:
        if role.get('committee_id'):
            committee = {'position': role.get('position').title(), 'name': role.get('committee')}
            committees.append(committee)
    return committees


def get_old_roles(legislator):
    old_roles = legislator.get('old_roles')
    ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])
    if old_roles:
        terms = [int(term.strip('th').strip('st').strip('rd')) for term in old_roles.keys()]
        latest = max(terms)
        latest_array = old_roles.get(ordinal(latest))
        committees = get_committee(latest_array)
        return ordinal(latest), committees
    else:
        return None, []


def nltk_process(word_list, filter_initial_letter):
    tokens = nltk.word_tokenize(' '.join(word_list))
    tagged = nltk.pos_tag(tokens)
    good_words = [word for word, pos_tag in tagged if not pos_tag.startswith(filter_initial_letter)]
    return good_words


def subject_list(bill_params):
    bill_r = requests.get(BILL_ENDPOINT, params=bill_params)
    # print(bill_r.url)
    relevant_bill_data = {'subjects': [], 'titles': []}
    if type(bill_r.json()) == list:
        for sunlight_bill in bill_r.json():
            if sunlight_bill['subjects']:
                relevant_bill_data['subjects'] += sunlight_bill['subjects']
            else:
                relevant_bill_data['subjects'].append('None')
            if sunlight_bill['title']:
                relevant_bill_data['titles'].append(sunlight_bill['title'])
    else:
        raise ValueError(type(bill_r.json()), bill_r.json())
    return relevant_bill_data

LEGIS_STYLE = Style(background='transparent',
                    plot_background='transparent',
                    transition='400ms ease-in')


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

    contrib_pie = pygal.Pie(show_legend=False, style=LEGIS_STYLE)
    contrib_pie.title = '% Total Contributions By Size'

    for cand in candidate_committees:
        # print(cand['candidate'])
        commitee_id = cand['committee_id']
        contrib_params = {'api_key' : OPEN_FEC_KEY,
                          'cycle' : election_year}
        contrib_r = requests.get(OPEN_FEC_ENDPOINT + '/committee/{0}/schedules/schedule_a/by_size/'.format(commitee_id), params=contrib_params)
        for contrib in contrib_r.json()['results']:
            # print(contrib)
            contrib_pie.add(contrib['size'], contrib['total'])

    return contrib_pie.render_data_uri()


SOCIAL_ENDPOINTS = {
    'Facebook' : 'https://www.facebook/com/',
    'Twitter' : 'https://twitter.com/',
    'YouTube' : 'https://www.youtube.com/user/',
    'GooglePlus' : 'https://plus.google.com/'
}


if __name__ == '__main__':
    app.run()
