import datetime
import os


API_KEY = 'AIzaSyCtLpZ3MKo33ziOynkUbDJwqvF_baYY1ls'
GOOGLE_CIVIC_KEY = 'AIzaSyDny6NNitDS3FIGkXWKO8sMgsNb9-G-h6E'
OS_API_KEY= 'f8686fdf6e4871299219f398f88d508a'
OPEN_FEC_KEY = 'FiiYWSsRi01pGXUNkfhwbEX6tF84AJpJq2zp3gzq'
PRO_PUBLICA_KEY = 'oCmlfzzjf14vd9eOG16H0aLG4wJLkRxn6GX54rRS'
DEFAULT_FONT = 'Helvetica-Light'

GOOGLE_GEOCODE_ENDPOINT = 'https://maps.googleapis.com/maps/api/geocode/json'
GOOGLE_CIVIC_ENDPOINT = 'https://www.googleapis.com/civicinfo/v2/representatives'
LEGISLATOR_ENDPOINT = 'http://openstates.org/api/v1/legislators/geo/'
BILL_ENDPOINT = 'http://openstates.org/api/v1/bills/'
COMMITTEE_ENDPOINT = 'http://openstates.org/api/v1/committees/{0}'
OPEN_FEC_ENDPOINT = 'https://api.open.fec.gov/v1'
PRO_PUBLICA_MEMBERS_ENDPOINT = 'https://api.propublica.org/congress/v1/115/{0}/members.json'
PRO_PUBLICA_MEMBER_VOTE_ENDPOINT = 'https://api.propublica.org/congress/v1/members/{0}/votes.json'
PRO_PUB_HEADERS = {'X-API-Key': PRO_PUBLICA_KEY}

CURRENT_YEAR = datetime.datetime.now().year

CUSTOM_FONT = os.path.join('static', 'Helvetica-Light.ttf')
BULMA_COLORS = ['is-success', 'is-info', 'is-primary', 'is-danger']

SOCIAL_ENDPOINTS = {
    'Facebook': 'https://www.facebook.com/',
    'Twitter': 'https://twitter.com/',
    'YouTube': 'https://www.youtube.com/user/',
    'GooglePlus': 'https://plus.google.com/'
}

PYGAL_COLORS = ['rgb(186,104,200)', 'rgb(247,123,114)', 'rgb(121,133,203)', 'rgb(77,181,172)', 'rgb(149,117,204)',
                'rgb(81,118,148)', 'rgb(224, 94, 85)', 'rgb(78, 150, 143)']

WHAT_WERE_DOING_MD = 'static/md/what_happen.md'
THANK_YOU_MD = 'static/md/thank_you.md'


MAX_BILLS_LENGTH = 7