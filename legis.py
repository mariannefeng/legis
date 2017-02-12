from flask import Flask, request, jsonify, render_template, Blueprint
import collections
import requests
import json
import datetime
import os
import io

from dateutil.relativedelta import relativedelta
import pygal
import nltk
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
from pygal.style import Style

app = Flask(__name__)
# create additional static directory
blueprint = Blueprint('clouds', __name__, static_url_path='/clouds', static_folder='clouds/')
app.register_blueprint(blueprint)

API_KEY = 'AIzaSyCtLpZ3MKo33ziOynkUbDJwqvF_baYY1ls'
GOOGLE_CIVIC_KEY = 'AIzaSyDny6NNitDS3FIGkXWKO8sMgsNb9-G-h6E'
OS_API_KEY= 'f8686fdf6e4871299219f398f88d508a'

GOOGLE_GEOCODE_ENDPOINT = 'https://maps.googleapis.com/maps/api/geocode/json'
GOOGLE_CIVIC_ENDPOINT = 'https://www.googleapis.com/civicinfo/v2/representatives'
LEGISLATOR_ENDPOINT = 'http://openstates.org/api/v1/legislators/geo/'
BILL_ENDPOINT = 'http://openstates.org/api/v1/bills/'
COMMITTEE_ENDPOINT = 'http://openstates.org/api/v1/committees/{0}'


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
                rep['party']  = civic_r.json()['officials'][index]['party']
                rep['chamber']  = office['name']
                rep['photo'] = civic_r.json()['officials'][index].get('photoUrl')
                rep['contact'] = {}
                rep['contact']['phone'] = civic_r.json()['officials'][index].get('phones')[0]
                address_map = civic_r.json()['officials'][index].get('address')[0]
                rep['contact']['address'] = '{0} {1}, {2} {3}'.format(address_map['line1'], address_map['city'],
                                                                      address_map['state'], address_map['zip'])
                rep['contact']['url'] = civic_r.json()['officials'][index].get('urls')[0]
                rep['social'] = civic_r.json()['officials'][index].get('channels')
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

        # one_year = datetime.datetime.now() + relativedelta(months=-12)
        # bill_params = {'sponsor_id': sunlight_id, 'updated_since': one_year.strftime('%Y-%m-%d')}

        # title_subject_data = subject_list(bill_params)
        # subject_count = collections.Counter(title_subject_data['subjects'])
        # title_words = ' '.join(title_subject_data['titles'])
        # print(title_words)
        # wordcloud = WordCloud(stopwords=STOPWORDS).generate(title_words)
        # rep['wordcloud'] = wordcloud
        ## PIE CHART
        # pie_chart = pygal.Pie(show_legend=False, style=LEGIS_STYLE)
        # pie_chart.title = 'Bills Speak Louder than Words'
        # for subject, count in subject_count.items():
        #     pie_chart.add(subject, count)
        # rep['chart'] = pie_chart.render_data_uri()
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



def make_bill_chart(sunlight_id):
    one_year = datetime.datetime.now() + relativedelta(months=-12)
    bill_params = {'sponsor_id': sunlight_id, 'updated_since': one_year.strftime('%Y-%m-%d')}
    title_subject_data = subject_list(bill_params)
    subject_count = collections.Counter(title_subject_data['subjects'])
    # if 'None" comprises 50%+ of total subject data, then render a word cloud of titles instead.
    if subject_count.most_common(1)[0][0] == 'None':
        # check if it is 50%
        composition = {subject: subject_count[subject]/float(len(title_subject_data['subjects'])) for subject in subject_count}
        print(composition)
        if composition.get('None') > .5:
            # get rid of verbs
            good_words = nltk_process(title_subject_data['titles'], 'V')
            # make word cloud
            cloud = WordCloud(height=300, width=600).generate(' '.join(good_words))
            filename = '{}.png'.format(sunlight_id)
            cloud.to_file(os.path.join('clouds', filename))
            return True, filename
    else:
        pie_chart = pygal.Pie(show_legend=False, style=LEGIS_STYLE)
        pie_chart.title = 'Bills Speak Louder than Words'
        for subject, count in subject_count.items():
            pie_chart.add(subject, count)
        return False, pie_chart.render_data_uri()


def nltk_process(word_list, filter_initial_letter):
    tokens = nltk.word_tokenize(' '.join(word_list))
    tagged = nltk.pos_tag(tokens)
    good_words = [word for word, pos_tag in tagged if not pos_tag.startswith(filter_initial_letter)]
    return good_words


def subject_list(bill_params):
    bill_r = requests.get(BILL_ENDPOINT, params=bill_params)
    print(bill_r.url)
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



if __name__ == '__main__':
    app.run()
