import requests

import VARS as vars
import chart_creation as charts

DATA_HOSTNAME = 'localhost'
DATA_PORT = '5000'


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
        if representatives:
            self.representatives = representatives
        else:
            self.representatives = []
        self.google_error = None

    def get_reps(self):
        url = 'http://{0}:{1}/'.format(DATA_HOSTNAME, DATA_PORT)
        params = {"google_address": self.google_address}
        # add federal reps
        federal = requests.get(url + vars.DATA_US_REPS_PATH, params=params).json()
        # no point in going further if the Google Civic API is unhappy
        if federal[0].get('error'):
            self.google_error = federal[0]["error"]["Google Civic Api"]
        else:
            create_charts(federal, 'FEDERAL')
            self.representatives += federal
            # get dat state sheit
            state = requests.get(url + vars.DATA_STATE_REPS_PATH, params=params).json()
            create_charts(state, 'STATE')
            self.representatives += state
        return self.representatives


def create_charts(reps, chart_type):
    for rep in reps:
        # create contrib chart with finance data generated
        if chart_type == 'FEDERAL':
            print(rep['finance'])
            contrib_list = rep['finance']['contrib']
            election_year = rep['finance']['election_year']
            rep['chart_image'] = charts.create_contribution_chart(contrib_list, election_year)
        elif chart_type == 'STATE':
            if rep['bill_chart_type'] == 'word_cloud':
                charts.create_word_cloud(rep['bill_chart_data'], rep['id'])

