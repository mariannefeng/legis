import os
import abc
import math
import datetime


import nltk
import requests
import requests_cache
import collections
import re
import xml.etree.ElementTree as ET

from dateutil.relativedelta import relativedelta

import legis_data.process.VARS as vars

# cache for requests
requests_cache.install_cache('test_cache', backend='sqlite', expire_after=300)


def get_house_members():
    master_house_list = {}
    house_r = requests.get(vars.PP_MEMBERS.format('house'), headers=vars.PP_HEADERS)
    for member in house_r.json()['results'][0]['members']:
        last_name_list = member['last_name'].split()
        parsed_last_name = last_name_list[len(last_name_list) - 1]
        name_key = ''.join(e for e in parsed_last_name if e.isalnum())

        lower_name_key = name_key.lower()
        lower_first_name = member['first_name'][0].lower()
        formatted_key = '{0}{1}{2}'.format(lower_name_key, lower_first_name[0], member['state'])
        master_house_list[formatted_key] = {}
        master_house_list[formatted_key]['id'] = member['id']
        master_house_list[formatted_key]['detail_url'] = member['api_uri']
    return master_house_list


def get_senate_members():
    master_senate_list = {}
    senate_r = requests.get(vars.PP_MEMBERS.format('senate'), headers=vars.PP_HEADERS)
    for member in senate_r.json()['results'][0]['members']:
        last_name_list = member['last_name'].split()
        parsed_last_name = last_name_list[len(last_name_list) - 1]
        name_key = ''.join(e for e in parsed_last_name if e.isalnum())

        lower_name_key = name_key.lower()
        lower_first_name = member['first_name'][0].lower()
        formatted_key = '{0}{1}{2}'.format(lower_name_key, lower_first_name[0], member['state'])
        master_senate_list[formatted_key] = {}
        master_senate_list[formatted_key]['id'] = member['id']
        master_senate_list[formatted_key]['detail_url'] = member['api_uri']
    return master_senate_list

# todo: we need a thread that's going to update this, maybe?
HOUSE_PROPUB = get_house_members()
SENATE_PROPUB = get_senate_members()


class Legislator:
    """Abstract class"""
    def __init__(self,
                 id=None,
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
                 bill_chart_data=None,
                 bill_chart_type=None,
                 state=None,
                 **kwargs):
        self.id = id
        self.name = name
        self.party = party
        self.chamber = chamber
        self.photo = photo
        self.state = state
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
        self.bill_chart_data = bill_chart_data

    @abc.abstractmethod
    def grab_all_data(self):
        """grab all related data"""
        return


class USLegislator(Legislator):
    """US Legislator"""
    def __init__(self,
                 id=None,
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
                 bill_chart_data=None,
                 bill_chart_type=None,
                 state=None):
        super().__init__(id, name, party, chamber, photo, bill_chart_data, level,
                         contact, social, committees, bill_chart_type, state,
                         old_term_ordinal, old_committees, bills)
        self.level = 'US'
        self.finance = finance

    def grab_all_data(self):
        self.get_financial_data()

    @staticmethod
    def __create_contrib_data(candidate_committees, election_year):
        contrib_data = []
        for cand in candidate_committees:
            commitee_id = cand['committee_id']
            contrib_params = {'api_key': vars.OPEN_FEC_KEY,
                              'cycle': election_year,
                              'sort': 'size'}
            contrib_r = requests.get('{0}/committee/{1}/schedules/schedule_a/by_size/'.format(vars.OPEN_FEC_ENDPOINT,
                                                                                              commitee_id),
                                     params=contrib_params)
            contrib_data.append(contrib_r.json())
        return contrib_data

    def __pull_contrib_totals(self, election_year):
        cand_overview = {}

        # create contributes breakdown by receipts + spending
        cand_total_params = {'api_key': vars.OPEN_FEC_KEY,
                             'cycle': election_year,
                             'q': self.name}
        cand_total_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/totals/', params=cand_total_params)
        cand_total = cand_total_r.json().get('results')
        if len(cand_total) == 0:
            name_list = self.name.split()
            cand_name_filter = {'q': name_list[len(name_list) - 1],
                                       'cycle': election_year,
                                       'state': self.state,
                                       'api_key': vars.OPEN_FEC_KEY}
            cand_total_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/totals/', params=cand_name_filter)
            cand_total = cand_total_r.json()['results']

        if len(cand_total) > 0:
            cand_overview['total_receipts'] = cand_total[0]['receipts']
            cand_overview['disbursements'] = cand_total[0]['disbursements']
            cand_overview['cash_on_hand'] = cand_total[0]['cash_on_hand_end_period']
            cand_overview['debt'] = cand_total[0]['debts_owed_by_committee']
        return cand_overview

    def __pull_contrib_chart_data(self, election_year):
        # create search filter based on full name from google civics
        committee_search_filter = {'q': self.name,
                                   'cycle': election_year,
                                   'api_key': vars.OPEN_FEC_KEY}
        committees_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/search/', params=committee_search_filter)
        name_committee_detail = committees_r.json()['results']

        # if could not find using full name from google civics, then search by last name + cycle + state
        if len(name_committee_detail) == 0:
            name_list = self.name.split()
            committee_search_filter = {'q': name_list[len(name_list) - 1],
                                       'cycle': election_year,
                                       'state': self.state,
                                       'api_key': vars.OPEN_FEC_KEY}
            committees_r = requests.get(vars.OPEN_FEC_ENDPOINT + '/candidates/search/', params=committee_search_filter)
            name_committee_detail = committees_r.json()['results']
        return name_committee_detail

    def get_financial_data(self):
        """create chart from FEC data and set it to finance attribute"""
        # find current election cycle year
        if vars.CURRENT_YEAR % 2 == 0:
            election_year = vars.CURRENT_YEAR
        else:
            election_year = vars.CURRENT_YEAR - 1

        name_committee_detail = self.__pull_contrib_chart_data(election_year)

        # sometimes people run for both house and senate. contrib values are the same so just grabs first one in
        # results list
        candidate_committees = []
        one_election = name_committee_detail[0]
        cand_comm = {'candidate': one_election['name'],
                     'committee_id': one_election['principal_committees'][0]['committee_id']}
        candidate_committees.append(cand_comm)

        self.finance = {'overall': self.__pull_contrib_totals(election_year),
                        'contrib': self.__create_contrib_data(candidate_committees, election_year),
                        'election_year': election_year}



class StateLegislator(Legislator):
    def __init__(self,
                 id=None,
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
                 bill_chart_data=None,
                 bill_chart_type=None,
                 state=None):
        super().__init__(id, name, party, chamber, photo, bill_chart_data,
                         contact, social, committees, bill_chart_type,
                         level, old_term_ordinal, old_committees, bills, state)
        self.level = 'State'

    def grab_all_data(self):
        self.discover_chart_data()

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

        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(math.floor(n/10) % 10 != 1)*(n % 10 < 4) * n % 10::4])
        if old_roles:
            terms = []
            for term in old_roles.keys():
                # strip add-ons and cut off number at first -
                no_adds = term.strip('th').strip('st').strip('rd')

                try:
                    dash_index = no_adds.index('-')
                except ValueError:
                    dash_index = -1

                if dash_index > 0:
                    term_start = no_adds[:dash_index]
                else:
                    term_start = term
                terms.append(int(term_start))

            latest = max(terms)
            latest_array = old_roles.get(ordinal(latest))
            self.old_committees = self.get_committee(latest_array)
            # print('OOOOLLLLDDDD')
            # print(self.old_committees)
            self.old_term_ordinal = ordinal(latest)

    @staticmethod
    def get_bill_info(bill_params):
        """openstates get subject data and title of bills
        :return: list relevant_bill_data"""
        bill_r = requests.get(vars.OP_BILLS, params=bill_params)
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

    def discover_chart_data(self):
        # todo: MAKE SURE THAT THIS NO LONGER CALLS GET BILL DATA TWICE (possibly use another rule)
        one_year = datetime.datetime.now() + relativedelta(months=-12)
        bill_params = {'sponsor_id': self.id, 'updated_since': one_year.strftime('%Y-%m-%d')}
        title_subject_data = get_title_subject(bill_params)
        subject_count = collections.Counter(title_subject_data['subjects'])

        # if 'None" comprises 50%+ of total subject data, then render a word cloud of titles instead.
        if find_none(subject_count.most_common(1)):
            # check if it is 50%
            composition = {subject: subject_count[subject]/float(len(title_subject_data['subjects']))
                           for subject in subject_count}
            if composition.get('None') > .5:
                # get rid of verbs
                self.bill_chart_data = nltk_process(title_subject_data['titles'], 'V')
                self.bill_chart_type = 'word_cloud'
        else:
            self.bill_chart_type = 'pie'


def create_us_leg_list(google_address):
    civic_info = get_google_civic_info(google_address)
    if civic_info.get('errors'):
        return [{"error": {"Google Civic Api": civic_info['error'].get('message')}}]
    us_leg_list = []
    state = civic_info['normalizedInput']['state']
    for office in civic_info['offices']:
        if office['divisionId'] != "ocd-division/country:us":
            for index in office['officialIndices']:
                rep = map_json_to_us_leg(civic_info['officials'][index], office['name'], state)
                rep.grab_all_data()
                us_leg_list.append(rep.__dict__)
    return us_leg_list


def create_state_leg_list(google_address):
    state_leg_list = []
    location = get_google_location(google_address)
    sunlight_payload = {'lat': location.get('lat'), 'long': location.get('lng')}
    # todo: probably need some error handling for this sunlight API
    r = requests.get(vars.OP_LEGISLATORS, params=sunlight_payload)
    legislators_info = r.json()
    for legislator in legislators_info:
        rep = map_json_to_state_leg(legislator)
        rep.grab_all_data()
        state_leg_list.append(rep.__dict__)
    return state_leg_list


def find_none(most_common):
    for item in most_common:
        if str(item[0]) == 'None':
            return True
    return False


def get_google_civic_info(google_address):
    civic_payload = {'address': google_address,
                     'key': vars.GOOGLE_CIVIC_KEY,
                     'levels': 'country'
    #                  'roles': 'legislatorupperbody',
    #                  'roles': 'legislatorlowerbody'
    }
    civic_r = requests.get(vars.GOOGLE_CIVIC_ENDPOINT, params=civic_payload)
    google_result = civic_r.json()
    return google_result


def get_google_location(google_address):
    payload = {'address': google_address, 'key': vars.API_KEY}
    r = requests.get(vars.GOOGLE_GEOCODE_ENDPOINT, params=payload)
    location = r.json()['results'][0]['geometry']['location']
    return location


def map_json_to_us_leg(mapper, chamber, state):
    rep = USLegislator()
    rep.name = mapper['name']
    rep.party = mapper['party']
    rep.state = state
    # rep.get_financial_data()
    rep.chamber = chamber

    full_name = rep.name.split()
    name_key = str.lower(full_name[len(full_name) - 1]) + str.lower(full_name[0][0]) + state
    name_key = ''.join(e for e in name_key if e.isalnum())

    if chamber == 'United States Senate':
        member_details = SENATE_PROPUB[name_key]['detail_url']
    else:
        member_details = HOUSE_PROPUB[name_key]['detail_url']

    country_comm_r = requests.get(member_details, headers=vars.PP_HEADERS)
    comms_current = []
    for comm in country_comm_r.json()['results'][0]['roles']:
        # todo: need to auto decide what is most recent
        if comm['congress'] == '115':
            comms_current = comm['committees']
            break

    rep.committees = [comm_curr for comm_curr in comms_current]

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
        social_endpoint = vars.SOCIAL_ENDPOINTS[type] + social['id']
        status = check_url(social_endpoint)
        if status and status < 400:
            rep_social['link'] = social_endpoint
            rep_social['type'] = type
            rep.social.append(rep_social)
    return rep


def map_json_to_state_leg(legislator):
    rep = StateLegislator()
    rep.id = legislator.get('id')
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
    return rep


def get_title_subject(bill_params):
    bill_r = requests.get(vars.OP_BILLS, params=bill_params)
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


class Bill:
    # TODO: Figure out which of these attributes *actually* belong in this abstract class
    def __init__(self,
                 bill_type,
                 sponsor=None,
                 id=None,
                 title=None,
                 actions=None,
                 subjects=None,
                 cosponsors=None,
                 additional_files=None):
        if not sponsor:
            sponsor = {}
        if not actions:
            actions = []
        if not additional_files:
            additional_files = []
        if not cosponsors:
            self.cosponsors = []
        self.type = bill_type
        self.sponsor = sponsor
        self.id = id
        self.title = title
        self.actions = actions
        self.subjects = subjects
        self.additional_files = additional_files

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def populate_from_sources(self, sources: dict):
        """populate attributes based on a dictionary. """
        raise NotImplementedError("abstract class")


class UsBill(Bill):
    def __init__(self,
                 bill_type,
                 sponsor=None,
                 id=None,
                 title=None,
                 actions=None,
                 subjects=None,
                 cosponsors=None,
                 floor_text=None,
                 additional_files=None):
        super().__init__(bill_type, sponsor, id, title, actions, subjects, cosponsors, additional_files)
        # not sure that this is applicable to all bills so putting it here.
        self.floor_text = floor_text

    def populate_from_sources(self, sources: dict):
        self._populate_from_floor_item(sources['floor_item'])
        self._populate_detail_from_propublica()

    def _populate_from_floor_item(self, floor_item):
        """

        :return: 
        """
        self.id = floor_item.attrib['id']
        self.title = floor_item.find('legis-num').text
        self.floor_text = floor_item.find("floor-text").text
        for file in floor_item.find('files'):
            self.additional_files.append(file.attrib['doc-url'])

    def _populate_detail_from_propublica(self):
        bill_trim = list(filter(lambda x: x.isalnum(), self.title))
        bill_detail = requests.get(vars.PP_BILL_DETAIL.format(''.join(bill_trim)), headers=vars.PP_HEADERS).json()
        results = bill_detail.get('results')
        if results:
            # TODO: there has to be a better way to add new key value pairs to dict
            # question: what do we get back from this endpoint?
            self.sponsor['sponsor_name'] = results[0].get('sponsor')
            self.sponsor['sponsor_uri'] = results[0].get('sponsor_uri')
            self.actions = results[0].get('actions')
            self.subjects = [results[0].get('primary_subject')]
            self.cosponsors = results[0].get('cosponsors')



class StateBill(Bill):
    def __init__(self,
             bill_type,
             state,
             sponsor=None,
             id=None,
             title=None,
             actions=None,
             subjects=None,
             cosponsors=None,
             additional_files=None):
    
        super().__init__(bill_type, sponsor, id, title, actions, subjects, 
                         cosponsors, additional_files)
        self.state = state
        self.subjects = []
        self.session = None
        self.chamber = None
        self.open_states_id = None
        self.update_time = None
        self.bill_url = None
        self.action_dates = None

    def populate_from_sources(self, sources: dict):
        self.populate_from_broad_search(sources)
        self._populate_nitty_gritty()    
        
    def populate_from_broad_search(self, net):
        self.id = net['bill_id']
        self.chamber = net['chamber']
        self.open_states_id = net['id']
        self.session = net['session']
        self.subjects = net['subjects']
        self.title = net['title']
        self.update_time = net['updated_at']
    
    def _populate_nitty_gritty(self):
        fields = "fields=sources,sponsors,scraped_subjects,action_dates"
        bill_detail = requests.get('{0}{1}/{2}'.format(vars.OP_BILLS, self.open_states_id, fields)).json()
        if bill_detail.get('sources'):
            self.bill_url = bill_detail['sources'][0].get('url')
        sponsors = bill_detail['sponsors']
        for sponsor in sponsors:
            if sponsor.get('type') == 'primary':
                self.sponsor = sponsor
            else:
                self.cosponsors.append(sponsor)
        self.subjects += bill_detail.get('scraped_subjects', [])
        self.action_dates = bill_detail.get('action_dates')
        
        

def get_bills_by_state(state: str, int_to_show: int):
    payload = {'state': state, 'search_window': 'session'}
    result = requests.get(vars.OP_BILLS, params=payload).json()
    latest = result[:int_to_show]
    billz = []
    for a_bill in latest:
        bill = StateBill(a_bill['type'][0], state)
        # populating everything takes forever...i thiink it should be a little expansion option maybe 
        # for a bill that you could care about. 
        bill.populate_from_broad_search(a_bill)
        billz.append(bill.__dict__)
    return billz


def get_upcoming_bills(valid_time_frame):
    fp = os.path.dirname(os.path.realpath(__file__))
    house_bill_file = os.path.join(fp, 'house_bills/' + valid_time_frame + '.xml')
    upcoming_bills = ET.parse(house_bill_file)
    root = upcoming_bills.getroot()
    this_week = []

    categories = root.findall('category')
    for category in categories:
        type = category.get('type')
        for floor_items in category:
            for floor_item in floor_items:
                bill = UsBill(type)
                bill.populate_from_sources({'floor_item': floor_item})
                this_week.append(bill.__dict__)
    return this_week


def nltk_process(word_list, filter_initial_letter):
    tokens = nltk.word_tokenize(' '.join(word_list))
    tagged = nltk.pos_tag(tokens)
    good_words = [word for word, pos_tag in tagged if not pos_tag.startswith(filter_initial_letter)]
    return good_words


# checks URL. Returns status code if connected, None if couldn't connected
def check_url(url):
    status_code = 500
    try:
        r = requests.head(url)
        status_code = r.status_code
    except:
        print("failed to connect")
    return status_code
