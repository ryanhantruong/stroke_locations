'''Utility functions for dealing with locations and distances'''
import itertools
import pandas as pd
import numpy as np
import geopy.distance as geodist
import datetime
import maps
import requests

def extract_locations(data):
    '''Get list of (lat, lng) tuples from dataframe'''
    recs = data[['Latitude', 'Longitude']].to_records(index=False)
    return [list(x) for x in recs]


def distance_matrix(row_locs, col_locs, row_names, col_names):
    '''
    Get straight line distances between locations, along with a cutoff value
        for each row which can be used to define "nearby" locations for that
        row, relative to the closest location
        row_locs, col_locs -- lists of (lat, lng) tuples
        row_names, col_names -- indices identifying locations
    '''
    dist_vals = [geodist.distance(l1, l2).miles
                 for l1, l2 in itertools.product(row_locs, col_locs)]
    dist_vals = np.reshape(dist_vals, (len(row_locs), len(col_locs)))
    out = pd.DataFrame(dist_vals, columns=col_names, index=row_names)
    out['Min_dist'] = out.min(axis=1)
    out['Cutoff'] = out.Min_dist.apply(lambda m: max(m * 1.5, m + 30))
    out = out.drop(columns='Min_dist')
    return out

def _to_gmap_coor(coors):
    return '|'.join([','.join([str(x) for x in y]) for y in coors])

def get_request(api_request):
    return requests.get(api_request).json()

def get_depart_time():
    ''' Return peak traffic time at 5:30PM in a weekday
        that is in the future, to be used as an argument for
        Google Maps Distance Matrix API departure_time'''
    today = datetime.datetime.today()
    tmrw = today + datetime.timedelta(days=1)
    while tmrw.weekday() >= 5: # saturday is 5, sunday is 6 
        tmrw += datetime.timedelta(days=1)
    peak_hour = datetime.time(17,30,0) # 5:30PM
    depart_time = datetime.datetime.combine(tmrw,peak_hour)
    return int(depart_time.timestamp())

def gmap_distance_matrix(origins,destinations,mode='driving-traffic'):
    if mode=='driving-traffic':
        mode = 'driving'
        depart_time = get_depart_time()
    else:
        depart_time = None
    api_template = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins={}&destinations={}'
    origins,destinations = _to_gmap_coor(origins),_to_gmap_coor(destinations)
    api_call = api_template.format(origins,destinations)
    if depart_time: api_call += "&departure_time={}".format(depart_time)
    api_call += "&key={}".format(maps.get_key())
    return get_request(api_call)
