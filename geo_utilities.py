'''Utility functions for dealing with locations and distances'''
import itertools
import pandas as pd
import numpy as np
import geopy.distance as geodist


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
