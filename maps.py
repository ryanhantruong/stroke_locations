'''Interact with google maps api'''
import os
import configparser
import googlemaps


def get_key(config_path='config'):
    """
    Get the Google API keys from an external config file
    It looks like this:

    [api]
    api_number=<your api number>

    """
    config = configparser.ConfigParser()
    config.read(os.path.join(config_path, 'google_maps.cfg'))
    key = config['api']['api_number']
    return key


def get_client():
    '''
    Get a googlemaps client object to use for multiple API calls
    '''
    return googlemaps.Client(get_key())


def get_hospital_location(searchterm, client=None):
    '''
    Use the Google Places API to get the address and coordinates for a hospital
        given a search term.
    '''
    if client is None:
        client = get_client()

    basic = ['formatted_address', 'geometry', 'name', 'types']
    results = googlemaps.places.find_place(client, searchterm, 'textquery',
                                           fields=basic)

    if results['status'] != 'OK':
        return {}

    top_candidates = []
    other_candidates = []
    for candidate in results['candidates']:
        if 'hospital' in candidate['types']:
            top_candidates.append(candidate)
        else:
            other_candidates.append(candidate)

    if len(top_candidates) > 0:
        hospital = top_candidates[0]
    elif len(other_candidates) > 0:
        hospital = other_candidates[0]
    else:
        return {}

    out = {}
    out['Name'] = hospital['name']
    out['Address'] = hospital['formatted_address']
    out['Latitude'] = hospital['geometry']['location']['lat']
    out['Longitude'] = hospital['geometry']['location']['lng']

    return out
