'''Get and store travel times from specified locations to hospitals'''
import os
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm
import geo_utilities as geo
import hospitals
import maps
from pathlib import Path
import population

TIMES_DIR = os.path.join('data', 'travel_times')
if not os.path.isdir(TIMES_DIR):
    os.makedirs(TIMES_DIR)
LARGE_LIMIT = 10


def _get_travel_times_csv(times_path, points, all_hospitals):
    times_path = Path(times_path)
    if times_path.exists():
        times = pd.read_csv(times_path)
        if 'LOC_ID' in times.columns: times.set_index('LOC_ID', inplace=True)
        return times
    else:
        #make one
        return points.assign(Need_Update=False).assign(
            **{c: np.nan
               for c in all_hospitals.index})


def set_update_status_in_travel_times_csv(times_path,
                                          point_ids=[],
                                          update_status=True):
    all_times = _get_travel_times_csv(times_path, None, None)
    point_ids_str = ', '.join(point_ids)
    print(f'Setting Need_Update to {update_status} for {point_ids_str}')
    all_times.loc[point_ids, 'Need_Update'] = update_status
    print(f'Saving {times_path}')
    all_times.to_csv(times_path)


def get_travel_times(point_file, allow_large=False, hospital_address=None):
    '''
    Get travel times from each of the points in the given file to nearby
        hospitals in the master hospital file
    '''
    points = population.load_points(point_file)
    if not allow_large and points.shape[0] > LARGE_LIMIT:
        point_count = points.shape[0]
        mes = f"Attempting to run on {point_count} points."
        max_count = point_count * 50
        mes += f'\nVerify you want to make up to {max_count} Google Maps calls'
        # max 25 calls per hospital type per point
        raise ValueError(mes)

    all_hospitals = hospitals.load_hospitals(hospital_address)

    all_times_path = os.path.join(TIMES_DIR, os.path.basename(point_file))
    all_times = _get_travel_times_csv(all_times_path, points, all_hospitals)

    prim_data = all_hospitals[all_hospitals.CenterType == 'Primary']
    comp_data = all_hospitals[all_hospitals.CenterType == 'Comprehensive']

    # Determine locations need to be calculated for
    # rows with all NaN values for all columns
    # or if user manually change specify Need_Update to True for a row
    # (see set_update_status_in_travel_times_csv())
    selected_points = all_times.loc[all_times[all_hospitals.index].isna().all(
        axis=1) | all_times.Need_Update, ["Latitude", "Longitude"]]
    pbar = tqdm(selected_points.iterrows(), total=selected_points.shape[0])
    for loc_id, point in pbar:
        pbar.set_description(f"Processing {loc_id}")
        point = point.to_frame().T
        prim_time = _get_travel_times_for_one_point(point, prim_data,
                                                    'Primaries')
        comp_time = _get_travel_times_for_one_point(point, comp_data,
                                                    'Comprehensives')
        times = prim_time.join(
            comp_time.drop(columns=['Latitude', 'Longitude']))
        all_times.update(times, overwrite=True)
        all_times.to_csv(all_times_path)


def _get_travel_times_for_one_point(point, some_hospitals, desc=None):
    '''
    Get travel times for a subset of hospitals (using only this subset to
        determine which are "nearby")
    '''
    point_locs = geo.extract_locations(point)
    hosp_locs = geo.extract_locations(some_hospitals)

    distances = geo.distance_matrix(point_locs, hosp_locs, point.index,
                                    some_hospitals.index)
    times = point[['Latitude', 'Longitude']].copy()

    client = maps.get_client()

    for i in times.index:
        hosps = distances.loc[i]
        include = hosps[hosps < hosps.Cutoff]
        if len(include) > 25:
            # distance_matrix can only take 25 destinations, and we shouldn't
            #   need to consider 25 hospitals anyway, so just drop farther away
            #   ones if they're still there after the cutoff
            include = include.sort_values().head(25)
        grid_loc = geo.extract_locations(point.loc[[i]])
        hosp_locs = geo.extract_locations(some_hospitals.loc[include.index])

        matrix = client.distance_matrix(origins=grid_loc,
                                        destinations=hosp_locs,
                                        mode='driving')

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

        matrix = client.distance_matrix(origins=grid_loc,
                                        destinations=hosp_locs,
                                        mode='driving')

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
    parser.add_argument('--allow_large',
                        action='store_true',
                        help='Allow more than 10 points')
    args = parser.parse_args()
    main(args)
