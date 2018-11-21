'''Load, manipulate, and write hospital location files'''
import os
import itertools
import pandas as pd
import numpy as np
from tqdm import tqdm
import geopy.distance as geodist
import download
import maps


HOSPITAL_DIR = os.path.join('data', 'hospitals')
MASTER_LIST = os.path.join(HOSPITAL_DIR, 'all.csv')
if not os.path.isdir(HOSPITAL_DIR):
    os.makedirs(HOSPITAL_DIR)

JC_URL = ("https://www.qualitycheck.org/file.aspx?FolderName=" +
          "StrokeCertification&c=1")


def load_hospitals(hospital_file):
    '''
    Read in the given relative filepath as a table of hospital information
    '''
    return pd.read_csv(hospital_file, sep='|').set_index('CenterID')


def master_list(update=False):
    '''
    Get the dataframe of all known hospitals, building it from Joint
        Commission certification if it doesn't exist, and optionally updating
        it to capture additions to the JC list.
    '''

    try:
        existing = load_hospitals(MASTER_LIST)
    except FileNotFoundError:
        columns = [
            'CenterID', 'CenterType',
            'OrganizationName', 'City', 'State', 'PostalCode',
            'Name', 'Address', 'Latitude', 'Longitude', 'Failed_Lookup',
            'destination', 'destinationID', 'transfer_time',
            'DTN_1st', 'DTN_Median', 'DTN_3rd',
            'DTP_1st', 'DTP_Median', 'DTP_3rd'
        ]
        existing = pd.DataFrame(columns=columns).set_index('CenterID')

    if update or existing.empty:
        jc_file = download.download_file(JC_URL, 'Joint Commission')
        jc_data = pd.read_excel(jc_file)

        program_map = {
            'Advanced Comprehensive Stroke Center    ': 'Comprehensive',
            'Advanced Primary Stroke Center          ': 'Primary',
            # Treatment of TSCs is undecided; taking conservative approach
            'Advanced Thrombectomy Capable Stroke Ctr': 'Primary',
        }
        jc_data['CenterType'] = jc_data.CertificationProgram.map(program_map)
        jc_data = jc_data.dropna()

        # For multiple certifications, keep the comprehensive line
        #   NOTE - This ignores effective dates under the assumption that all
        #           listed certifications are active
        jc_data = jc_data.sort_values('CenterType')

        jc_data = jc_data.drop_duplicates(subset=['OrganizationId', 'City',
                                                  'State', 'PostalCode'])

        update_index = ['OrganizationName', 'City', 'State', 'PostalCode']
        jc_data = jc_data.set_index(update_index, verify_integrity=True)

        existing = existing.reset_index().set_index(update_index)

        new = jc_data[~jc_data.index.isin(existing.index)]
        new.Failed_Lookup = False
        out = pd.concat([existing, new], sort=False)
        out.update(jc_data)
        out = out.reset_index()

        next_ID = out.CenterID.max() + 1
        if pd.isnull(next_ID):
            next_ID = 1
        for i in out.index:
            if pd.isnull(out.CenterID[i]):
                out.loc[i, 'CenterID'] = next_ID
                next_ID += 1

        out.CenterID = out.CenterID.astype(int)
        out = out.set_index('CenterID', verify_integrity=True)
        _save_master_list(out)
    else:
        out = existing

    return out


def _save_master_list(data):
    data.to_csv(MASTER_LIST, sep='|')


def update_locations():
    '''
    Use google maps to find addresses and coordinates for any hospitals that
        don't yet have them, meaning all of 'Name', 'Address', 'Latitude', and
        'Longitude' are NaN. If any of these are filled the hospital will be
        skipped. To perform manual updates directly edit `all.csv`; the
        function `maps.get_hospital_location` can be used to manually generate
        address and location from any search string.
    '''
    current = master_list()

    loc_cols = ['Name', 'Address', 'Latitude', 'Longitude']
    no_data = current[loc_cols].isnull().all(axis=1)
    to_update = current[no_data & ~current.Failed_Lookup].index

    if to_update.empty:
        print('No locations to update')
        return

    client = maps.get_client()
    for i in tqdm(to_update, desc='Getting Locations'):
        orgname = current.OrganizationName[i]
        city = current.City[i]
        state = current.State[i]
        postal = current.PostalCode[i]

        searchterm = ' '.join([orgname, city, state, postal])

        results = maps.get_hospital_location(searchterm, client)

        if not results:
            tqdm.write(f"Found no results for {i}: '{searchterm}'")
            current.loc[i, 'Failed_Lookup'] = True
        else:
            current.loc[i, 'Name'] = results['Name']
            current.loc[i, 'Address'] = results['Address']
            current.loc[i, 'Latitude'] = results['Latitude']
            current.loc[i, 'Longitude'] = results['Longitude']
            current.loc[i, 'Failed_Lookup'] = False

        # save after each iteration to minimize data loss on crash/cancel
        _save_master_list(current)


def update_transfer_destinations():
    '''
    Use google maps to find transfer destinations for all primary hospitals
        that don't yet have one stored. Doesn't overwrite any data.
    '''
    data = master_list()
    # Only consider hospitals with location information
    data = data[~data[['Latitude', 'Longitude']].isnull().any(axis=1)]
    prim_data = data[data.CenterType == 'Primary']
    # Only find destinations for primaries that don't have one recorded
    trans_cols = ['destination', 'destinationID', 'transfer_time']
    prim_data = prim_data[prim_data[trans_cols].isnull().any(axis=1)]
    if prim_data.empty:
        print('No primaries to find transfer destinations for')
        return
    comp_data = data[data.CenterType == 'Comprehensive']

    prim_locs = _extract_locations(prim_data)
    comp_locs = _extract_locations(comp_data)

    distances = _distance_matrix(prim_locs, comp_locs, prim_data.index,
                                 comp_data.index)

    client = maps.get_client()
    for i in tqdm(prim_data.index):
        comps = distances.loc[i]
        include = comps[comps < comps.Cutoff]
        prim_loc = _extract_locations(prim_data.loc[[i]])
        comp_locs = _extract_locations(comp_data.loc[include.index])

        results = maps.get_transfer_destination(prim_loc, comp_locs, client)

        if not results:
            name = prim_data.Name[i]
            tqdm.write(f'Failed to find transfer dest for {i}: {name}')
            data.loc[i, 'destination'] = 'Unknown'
        else:
            time = results['transfer_time']
            if pd.isnull(time):
                hospital_id = np.NaN
                hospital_name = np.NaN
            else:
                hospital_index = results['destination_index']
                hospital_id = include.index[hospital_index]
                hospital_name = data.loc[hospital_id, 'Name']

            data.loc[i, 'transfer_time'] = time
            data.loc[i, 'destinationID'] = hospital_id
            data.loc[i, 'destination'] = hospital_name

        # save after each iteration to minimize data loss on crash/cancel
        _save_master_list(data)


def _extract_locations(data):
    '''Get list of (lat, lng) tuples from dataframe'''
    recs = data[['Latitude', 'Longitude']].to_records(index=False)
    return [list(x) for x in recs]


def _distance_matrix(row_locs, col_locs, row_names, col_names):
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
