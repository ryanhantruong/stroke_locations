'''Interact with google maps api'''
import os
import configparser
import googlemaps
import numpy as np
import pandas as pd


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


def get_transfer_destination(location, candidates, client=None):
    '''
    Given the location of a primary center and a dataframe of distances to
        comprehensive centers, return the index the optimal destination and the
        time it will take to get there.
        Location and candidates should both be lists of (lat, lng) tuples
        Uses the distance matrix API without traffic information
    '''
    if client is None:
        client = get_client()

    matrix = client.distance_matrix(
        origins=location,
        destinations=candidates,
        mode='driving'
    )

    out = {}
    if matrix['status'] != 'OK' or len(matrix['rows']) != 1:
        return out

    elements = matrix['rows'][0]['elements']
    times = []
    for el in elements:
        if el['status'] == 'OK':
            times.append(el['duration']['value'] / 60)
        else:
            times.append(np.NaN)

    time = min(times)
    if pd.isnull(time):
        hospital_index = np.NaN
    else:
        hospital_index = times.index(time)

    out['transfer_time'] = time
    out['destination_index'] = hospital_index

    return out
