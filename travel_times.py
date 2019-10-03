'''Get and store travel times from specified locations to hospitals'''
import os
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm
import geo_utilities as geo
import hospitals
import maps


TIMES_DIR = os.path.join('data', 'travel_times')
if not os.path.isdir(TIMES_DIR):
    os.makedirs(TIMES_DIR)
LARGE_LIMIT = 10


def get_travel_times(point_file, allow_large=False,hospital_address=None):
    '''
    Get travel times from each of the points in the given file to nearby
        hospitals in the master hospital file
    '''
    points = pd.read_csv(point_file).set_index('LOC_ID')
    if not allow_large and points.shape[0] > LARGE_LIMIT:
        point_count = points.shape[0]
        mes = f"Attempting to run on {point_count} points."
        max_count = point_count * 50
        mes += f'\nVerify you want to make up to {max_count} Google Maps calls'
        # max 25 calls per hospital type per point
        raise ValueError(mes)

    if hospital_address is None:
        all_hospitals = hospitals.master_list_han()
    else:
        all_hospitals = pd.read_csv(hospital_address,sep='|')
    all_hospitals.set_index('HOSP_ID',inplace=True)

    prim_data = all_hospitals[all_hospitals.CenterType == 'Primary']
    comp_data = all_hospitals[all_hospitals.CenterType == 'Comprehensive']

    prim_times = _get_travel_times(points, prim_data, 'Primaries')
    comp_times = _get_travel_times(points, comp_data, 'Comprehensives')

    all_times = prim_times.join(comp_times.drop(columns=['Latitude',
                                                         'Longitude']))

    points_name = os.path.basename(point_file)
    all_times.to_csv(os.path.join(TIMES_DIR, points_name))


def _get_travel_times(points, some_hospitals, desc=None):
    '''
    Get travel times for a subset of hospitals (using only this subset to
        determine which are "nearby")
    '''
    point_locs = geo.extract_locations(points)
    hosp_locs = geo.extract_locations(some_hospitals)

    distances = geo.distance_matrix(point_locs, hosp_locs, points.index,
                                    some_hospitals.index)
    times = points[['Latitude', 'Longitude']].copy()

    client = maps.get_client()

    for i in tqdm(times.index, desc=desc):
        hosps = distances.loc[i]
        include = hosps[hosps < hosps.Cutoff]
        if len(include) > 25:
            # distance_matrix can only take 25 destinations, and we shouldn't
            #   need to consider 25 hospitals anyway, so just drop farther away
            #   ones if they're still there after the cutoff
            include = include.sort_values().head(25)
        grid_loc = geo.extract_locations(points.loc[[i]])
        hosp_locs = geo.extract_locations(some_hospitals.loc[include.index])

        matrix = client.distance_matrix(
            origins=grid_loc,
            destinations=hosp_locs,
            mode='driving'
        )

        for this_row in matrix['rows']:

            elements = this_row['elements']
            for j, el in enumerate(elements):
                col = include.index[j]
                if el['status'] == 'OK':
                    val = el['duration']['value'] / 60
                else:
                    val = np.NaN
                times.loc[i, col] = val

    return times


def main(args):
    point_file = args.point_file
    allow_large = args.allow_large
    get_travel_times(point_file, allow_large)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('point_file', help='Path to locations')
    parser.add_argument('--allow_large', action='store_true',
                        help='Allow more than 10 points')
    args = parser.parse_args()
    main(args)
