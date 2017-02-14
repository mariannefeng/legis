import os
import math
import random
import datetime
import re

import nltk
import pygal
import requests
import collections
from pygal.style import Style
from wordcloud import WordCloud, STOPWORDS
from dateutil.relativedelta import relativedelta
#gittest
import VARS as vars

def get_house_members():
    master_house_list = {}
    house_r = requests.get(vars.PRO_PUBLICA_MEMBERS_ENDPOINT.format('house'), headers=vars.PRO_PUB_HEADERS)
    for member in house_r.json()['results'][0]['members']:
        last_name_list = member['last_name'].split()
        parsed_last_name = last_name_list[len(last_name_list) - 1]
        name_key = ''.join(e for e in parsed_last_name if e.isalnum())
        master_house_list['{0}{1}{2}'.format(name_key.lower(),
                                             member['first_name'][0].lower(),
                                             member['state'])] = {}
        master_house_list['{0}{1}{2}'.format(name_key.lower(), member['first_name'][0].lower(), member['state'])]['id'] = member['id']
        master_house_list['{0}{1}{2}'.format(name_key.lower(), member['first_name'][0].lower(), member['state'])]['detail_url'] = member['api_uri']
    return master_house_list

def get_senate_members():
    master_senate_list = {}
    senate_r = requests.get(vars.PRO_PUBLICA_MEMBERS_ENDPOINT.format('senate'), headers=vars.PRO_PUB_HEADERS)
    for member in senate_r.json()['results'][0]['members']:
        last_name_list = member['last_name'].split()
        parsed_last_name = last_name_list[len(last_name_list) - 1]
        name_key = ''.join(e for e in parsed_last_name if e.isalnum())
        master_senate_list['{0}{1}{2}'.format(name_key.lower(), member['first_name'][0].lower(), member['state'])] = {}
        master_senate_list['{0}{1}{2}'.format(name_key.lower(), member['first_name'][0].lower(), member['state'])]['id'] = member['id']
        master_senate_list['{0}{1}{2}'.format(name_key.lower(), member['first_name'][0].lower(), member['state'])]['detail_url'] = member['api_uri']
    return master_senate_list

HOUSE_PROPUB = get_house_members()
SENATE_PROPUB = get_senate_members()


class Constituent:
    """Class representing the politically-curious human
    currently methods are just the google methods, but I figure we might do more later,
    maybe we can save constituent info so people can tag what is important to them or something

    :param address: House Number / Street Info
    :param state: State they reside in
    :param city: City they reside in

    :param google_address: formatted address for Google API
    :param representatives: List of representatives that represent this Constituent

    :method get_google_civic_info:
        return the result of google's civic API on countrywide scale based on the address

    :method get_google_location:
        return dict of {'lat': latitude, 'lng': longitude} based on address
    """
    def __init__(self, address, city, state, representatives=None):
        self.address = address
        self.city = city
        self.state = state
        self.google_address = '{0}, {1}, {2}'.format(self.address, self.city, self.state)
        self.location = self.get_google_location()
        if representatives:
            self.representatives = representatives
        else:
            self.representatives = []
        self.google_error = None

    def get_google_civic_info(self):
        civic_payload = {'address': self.google_address,
                         'key': vars.GOOGLE_CIVIC_KEY,
                         'levels': 'country'
        #                  'roles': 'legislatorupperbody',
        #                  'roles': 'legislatorlowerbody'
        }
        civic_r = requests.get(vars.GOOGLE_CIVIC_ENDPOINT, params=civic_payload)
        google_result = civic_r.json()
        if google_result.get('error'):
            self.google_error = google_result['error'].get('message')
        return google_result

    def get_google_location(self):
        payload = {'address': self.google_address, 'key': vars.API_KEY}
        r = requests.get(vars.GOOGLE_GEOCODE_ENDPOINT, params=payload)
        location = r.json()['results'][0]['geometry']['location']
        return location


class Legislator:
    """Abstract class"""
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
    """US Legislator"""
    def __init__(self,
                 name=None,
                 party=None,
                 chamber=None,
                 photo=None,
                 contact=None,
                 social=None,
                 committees=None,
                 level=None,
                 finance=None,
                 old_term_ordinal=None,
                 old_committees=None,
                 bills=None,
                 bill_chart=None,
                 bill_chart_type=None):
        super().__init__(name, party, chamber, photo, bill_chart,
                         contact, social, committees, bill_chart_type,
                         old_term_ordinal, old_committees, bills, finance)
        self.level = 'US'
        self.finance = finance

    @staticmethod
    def __create_contrib_chart(candidate_committees, election_year):
        # create contributions breakdown by size
        contrib_bar = pygal.HorizontalBar(style=vars.FINANCE_BAR_STYLE,
                                          max_scale=4,
                                          js=[],
                                          print_values=True,
                                          print_values_position='center',
                                          value_formatter=lambda x: '${:20,.2f}'.format(x))
        contrib_bar.title = 'Total Contributions By Size - ' + str(election_year)

        for cand in candidate_committees:
            commitee_id = cand['committee_id']
            contrib_params = {'api_key' : vars.OPEN_FEC_KEY,
                              'cycle' : election_year,
                              'sort' : 'size'}
            contrib_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/committee/{0}/schedules/schedule_a/by_size/'.format(commitee_id), params=contrib_params)
            for i, contrib in enumerate(contrib_r.json()['results']):
                if i == 0:
                    contrib_bar.add(str(contrib['size']) + '-' + str(contrib_r.json()['results'][i + 1]['size']), contrib['total'])
                elif i == len(contrib_r.json()['results']) - 1:
                    contrib_bar.add(str(contrib['size']) + '+', contrib['total'])
                else:
                    contrib_bar.add(str(contrib['size']) + '-' + str(contrib_r.json()['results'][i + 1]['size']), contrib['total'])
        return contrib_bar.render_data_uri()

    @staticmethod
    def __pull_contrib_totals(name, state, election_year):
        cand_overview = {}

        # create contributes breakdown by receipts + spending
        cand_total_params = {'api_key': vars.OPEN_FEC_KEY,
                             'cycle': election_year,
                             'q': name}
        cand_total_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/totals/', params=cand_total_params)
        print(cand_total_r.url)
        cand_total = cand_total_r.json().get('results')
        if len(cand_total) == 0:
            name_list = name.split()
            print(name_list)
            cand_name_filter = {'q': name_list[len(name_list) - 1],
                                       'cycle': election_year,
                                       'state': state,
                                       'api_key': vars.OPEN_FEC_KEY}
            cand_total_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/totals/', params=cand_name_filter)
            cand_total = cand_total_r.json()['results']

        if len(cand_total) > 0:
            cand_overview['total_receipts'] = cand_total[0]['receipts']
            cand_overview['disbursements'] = cand_total[0]['disbursements']
            cand_overview['cash_on_hand'] = cand_total[0]['cash_on_hand_end_period']
            cand_overview['debt'] = cand_total[0]['debts_owed_by_committee']
        return cand_overview

    @staticmethod
    def __pull_contrib_chart_data(name, state, election_year):
        # create search filter based on full name from google civics
        committee_search_filter = {'q': name,
                                   'cycle': election_year,
                                   'api_key': vars.OPEN_FEC_KEY}
        committees_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/search/', params=committee_search_filter)
        name_committee_detail = committees_r.json()['results']

        # if could not find using full name from google civics, then search by last name + cycle + state
        if len(name_committee_detail) == 0:
            name_list = name.split()
            committee_search_filter = {'q': name_list[len(name_list) - 1],
                                       'cycle': election_year,
                                       'state': state,
                                       'api_key': vars.OPEN_FEC_KEY}
            committees_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/search/', params=committee_search_filter)
            name_committee_detail = committees_r.json()['results']
        return name_committee_detail

    def get_financial_data(self, name, state):
        """create chart from FEC data and set it to finance attribute"""
        # find current election cycle year
        if vars.CURRENT_YEAR % 2 == 0:
            election_year = vars.CURRENT_YEAR
        else:
            election_year = vars.CURRENT_YEAR - 1

        name_committee_detail = self.__pull_contrib_chart_data(name, state, election_year)

        candidate_committees = []
        for result in name_committee_detail:
            cand_comm = {'candidate': result['name'],
                         'committee_id': result['principal_committees'][0]['committee_id']}
            candidate_committees.append(cand_comm)

        self.finance = {'overall': self.__pull_contrib_totals(name, state, election_year),
                        'contrib': self.__create_contrib_chart(candidate_committees, election_year)}


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
        """Specific to OpenStates API, get committe info (position held, name of committee) based
        given a open states role array
         :return: list of committees
        """
        committees = []
        if role_array:
            for role in role_array:
                if role.get('committee_id'):
                    committee = {'position': role.get('position').title(), 'name': role.get('committee')}
                    committees.append(committee)
        return committees

    def set_old_roles(self, legislator):
        """Grab committees from latest committee info on hand"""
        old_roles = legislator.get('old_roles')
        ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])
        if old_roles:
            print(old_roles.keys())
            terms = [int(term.strip('th').strip('st').strip('rd')) for term in old_roles.keys()]
            # terms = [term.strip('th').strip('st').strip('rd') for term in old_roles.keys()]
            latest = max(terms)
            latest_array = old_roles.get(ordinal(latest))
            self.old_committees = self.get_committee(latest_array)
            self.old_term_ordinal = ordinal(latest)

    @staticmethod
    def get_bill_info(bill_params):
        """openstates get subject data and title of bills
        :return: list relevant_bill_data"""
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
                cloud = WordCloud(font_path=vars.CUSTOM_FONT, height=400, width=400, background_color="#f5f5f5").generate(' '.join(good_words))
                filename = '{}.png'.format(sunlight_id)
                cloud.recolor(color_func=turq_color_func, random_state=3).to_file(os.path.join('clouds', filename))
                self.bill_chart_type = 'word_cloud'
                self.bill_chart = filename
        else:
            pie_chart = pygal.Pie(show_legend=False, style=vars.BILL_CHART_STYLE, opacity_hover=.9)
            pie_chart.force_uri_protocol = 'http'
            pie_chart.title = 'Bills Speak Louder than Words'
            for subject, count in subject_count.items():
                pie_chart.add(subject, count)
            self.bill_chart_type = 'pie'
            self.bill_chart = pie_chart.render_data_uri()


def map_json_to_us_leg(mapper, chamber, state):
    rep = USLegislator()
    rep.name = mapper['name']
    rep.party = mapper['party']
    rep.get_financial_data(rep.name, state)
    rep.chamber = chamber

    print(rep.name)

    full_name = rep.name.split()
    name_key = str.lower(full_name[len(full_name) - 1]) + str.lower(full_name[0][0]) + state
    name_key = ''.join(e for e in name_key if e.isalnum())

    if chamber == 'United States Senate':
        member_details = SENATE_PROPUB[name_key]['detail_url']
    else:
        member_details = HOUSE_PROPUB[name_key]['detail_url']

    country_comm_r = requests.get(member_details, headers=vars.PRO_PUB_HEADERS)
    comms_current = []
    for comm in country_comm_r.json()['results'][0]['roles']:
        if comm['congress'] == '115':
            comms_current = comm['committees']
            break

    for comm_curr in comms_current:
        rep.committees.append(comm_curr)

    # votes_r = requests.get(PRO_PUBLICA_MEMBER_VOTE_ENDPOINT.format(pro_pub_id), params=PRO_PUB_PARAMS)
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


def nltk_process(word_list, filter_initial_letter):
    tokens = nltk.word_tokenize(' '.join(word_list))
    tagged = nltk.pos_tag(tokens)
    good_words = [word for word, pos_tag in tagged if not pos_tag.startswith(filter_initial_letter)]
    return good_words


def turq_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return random.choice(vars.PYGAL_COLORS)


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "hsl(0, 0%%, %d%%)" % random.randint(60, 90)
