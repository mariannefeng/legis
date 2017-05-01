# backend work supporting new vue. har. har


import requests
import legis_data.process.VARS as vars

class BasicCongressional:
    def __init__(self,
                 name=None,
                 chamber=None,
                 office=None,
                 party=None,
                 phone=None,
                 photo=None,
                 social=None):
        self.social = []

    def load_data(self, l, chamber):
        self.name = l['name']
        self.chamber = chamber
        self.office = l['address']
        self.party = l['party']
        self.phone = l['phones']
        self.photo = l['photoUrl']

        for social in l['channels']:
            rep_social = {}
            type = social['type']
            social_endpoint = vars.SOCIAL_ENDPOINTS[type] + social['id']
            status = check_url(social_endpoint)
            if status and status < 400:
                rep_social['link'] = social_endpoint
                rep_social['type'] = type
                self.social.append(rep_social)

        return self


# retrieve reps - involves initiating some BasicCongressional's
def get_reps(state):
    ocd_id='ocd-division%2Fcountry%3Aus%2Fstate:' + state.lower()
    civic_payload = {'recursive': True,
                     'key': vars.GOOGLE_CIVIC_KEY,
                     'levels': 'country'}
    civic_r = requests.get(vars.GOOGLE_CIVIC_ENDPOINT + '/' + ocd_id, params=civic_payload)
    google_result = civic_r.json()
    reps = []
    for office in google_result['offices']:
        for index in office['officialIndices']:
            rep = BasicCongressional()
            rep.load_data(google_result['officials'][index], office['name'])
            reps.append(rep.__dict__)
    return reps


# checks URL. Returns status code if connected, None if couldn't connected
def check_url(url):
    status_code = 500
    try:
        r = requests.head(url)
        status_code = r.status_code
    except:
        print("failed to connect")
    return status_code

