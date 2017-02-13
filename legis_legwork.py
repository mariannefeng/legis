import os
import math
import random
import datetime

import nltk
import pygal
import requests
import collections
from pygal.style import Style
from wordcloud import WordCloud, STOPWORDS
from dateutil.relativedelta import relativedelta

import VARS as vars


class Legislator:
    def __init__(self,
                 name=None,
                 party=None,
                 chamber=None,
                 photo=None,
                 contact=None,
                 social=None,
                 committees=None,
                 level=None,
                 old_term_ordinal=None,
                 old_committees=None,
                 bills=None,
                 bill_chart=None,
                 bill_chart_type=None,
                 **kwargs):
        self.name = name
        self.party = party
        self.chamber = chamber
        self.photo = photo
        if contact:
            self.contact = contact
        else:
            self.contact = {}
        if social:
            self.social = social
        else:
            self.social = []
        if committees:
            self.committees = committees
        else:
            self.committees = []
        if bills:
            self.bills = bills
        else:
            self.bills = []
        if old_committees:
            self.old_committees = old_committees
        self.level = level
        self.old_term_ordinal = old_term_ordinal
        self.bill_chart_type = bill_chart_type
        self.bill_chart = bill_chart

class USLegislator(Legislator):
    def __init__(self,
                 name=None,
                 party=None,
                 chamber=None,
                 photo=None,
                 contact=None,
                 social=None,
                 committees=None,
                 level=None,
                 old_term_ordinal=None,
                 old_committees=None,
                 bills=None,
                 bill_chart=None,
                 bill_chart_type=None,
                 contrib_chart=None):
        super().__init__(name, party, chamber, photo, bill_chart,
                         contact, social, committees, bill_chart_type,
                         old_term_ordinal, old_committees, bills)
        self.level = 'US'
        self.contrib_chart = contrib_chart

    def get_financial_data(self, names):
        if vars.CURRENT_YEAR % 2 == 0:
            election_year = vars.CURRENT_YEAR
        else:
            election_year = vars.CURRENT_YEAR - 1
        committee_search_filter = {'q': names,
                                   'cycle' : election_year,
                                   'api_key': OPEN_FEC_KEY}
        committees_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/search/', params=committee_search_filter)
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
            contrib_params = {'api_key' : vars.OPEN_FEC_KEY,
                              'cycle' : election_year}
            contrib_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/committee/{0}/schedules/schedule_a/by_size/'.format(commitee_id), params=contrib_params)
            for contrib in contrib_r.json()['results']:
                # print(contrib)
                contrib_pie.add(contrib['size'], contrib['total'])
        self.contrib_chart = contrib_pie.render_data_uri()


class StateLegislator(Legislator):
    def __init__(self,
                 name=None,
                 party=None,
                 chamber=None,
                 photo=None,
                 contact=None,
                 social=None,
                 committees=None,
                 level=None,
                 old_term_ordinal=None,
                 old_committees=None,
                 bills=None,
                 bill_chart=None,
                 bill_chart_type=None):
        super().__init__(name, party, chamber, photo, bill_chart,
                         contact, social, committees, bill_chart_type,
                         level, old_term_ordinal, old_committees, bills)
        self.level = 'State'

    def load_committees(self):
        pass

    def get_committee(self, role_array):
        committees = []
        for role in role_array:
            if role.get('committee_id'):
                committee = {'position': role.get('position').title(), 'name': role.get('committee')}
                committees.append(committee)
        return committees

    def set_old_roles(self, legislator):
        old_roles = legislator.get('old_roles')
        ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])
        if old_roles:
            terms = [int(term.strip('th').strip('st').strip('rd')) for term in old_roles.keys()]
            latest = max(terms)
            latest_array = old_roles.get(ordinal(latest))
            self.old_committees = self.get_committee(latest_array)
            self.old_term_ordinal = ordinal(latest)

    def get_bill_info(self, bill_params):
        bill_r = requests.get(vars.BILL_ENDPOINT, params=bill_params)
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

    def create_chart(self, sunlight_id):
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
                cloud = WordCloud(font_path=vars.CUSTOM_FONT, height=400, width=400, background_color="#ffffff").generate(' '.join(good_words))
                filename = '{}.png'.format(sunlight_id)
                cloud.recolor(color_func=grey_color_func, random_state=3).to_file(os.path.join('clouds', filename))
                self.bill_chart_type = 'word_cloud'
                self.bill_chart = filename
        else:
            pie_chart = pygal.Pie(show_legend=False, style=LEGIS_STYLE, opacity_hover=.9)
            pie_chart.force_uri_protocol = 'http'
            pie_chart.title = 'Bills Speak Louder than Words'
            for subject, count in subject_count.items():
                pie_chart.add(subject, count)
            self.bill_chart_type = 'pie'
            self.bill_chart = pie_chart.render_data_uri()


def map_json_to_us_leg(mapper, chamber):
    rep = USLegislator()
    rep.name = mapper['name']
    rep.party = mapper['party']
    rep.chamber = chamber
    rep.photo = mapper.get('photoUrl')
    rep.contact['phone'] = mapper.get('phones')[0]
    address_map = mapper.get('address')[0]
    rep.contact['address'] = '{0} {1}, {2} {3}'.format(address_map['line1'], address_map['city'],
                                                       address_map['state'], address_map['zip'])
    rep.contact['url'] = mapper.get('urls')[0]

    for social in mapper.get('channels'):
        rep_social = {}
        type = social['type']
        rep_social['type'] = type
        rep_social['link'] = vars.SOCIAL_ENDPOINTS[type] + social['id']
        rep.social.append(rep_social)
    return rep


def map_json_to_state_leg(legislator):
    rep = StateLegislator()
    rep.name = legislator.get('full_name')
    rep.party = legislator.get('party')
    rep.photo = legislator.get('photo_url')
    rep.chamber = 'House' if legislator.get('chamber') == 'lower' else 'Senate'
    # MULTIPLE OFFICES? right now just taking the first in array
    rep.contact = legislator.get('offices')[0]
    rep.contact['url'] = legislator.get('url')
    rep.contact.pop('fax')
    rep.contact.pop('name')
    rep.contact.pop('type')
    #  get committee info
    rep.committees = rep.get_committee(legislator.get('roles'))
    if not rep.committees:
        rep.set_old_roles(legislator)

    # # pull legislator id for bill info
    sunlight_id = legislator.get('id')
    rep.create_chart(sunlight_id)
    return rep


def subject_list(bill_params):
    bill_r = requests.get(vars.BILL_ENDPOINT, params=bill_params)
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


def nltk_process(word_list, filter_initial_letter):
    tokens = nltk.word_tokenize(' '.join(word_list))
    tagged = nltk.pos_tag(tokens)
    good_words = [word for word, pos_tag in tagged if not pos_tag.startswith(filter_initial_letter)]
    return good_words


def turq_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    pastels = ["rgb(64,224,208)", "rgb(0,255,255)","rgb(224,255,255)", "rgb(95,158,160)"]
    return random.choice(pastels)


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "hsl(0, 0%%, %d%%)" % random.randint(60, 90)
