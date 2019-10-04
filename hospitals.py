'''Load, manipulate, and write hospital location files'''
import pandas as pd
import numpy as np
from tqdm import tqdm
import download
import maps
import geo_utilities as geo
from pathlib import Path
import data_io

HOSPITAL_DIR = Path('data') / 'hospitals'
if not HOSPITAL_DIR.exists(): HOSPITAL_DIR.mkdir()
MASTER_LIST = HOSPITAL_DIR / 'all.csv'
MASTER_LIST_OFFLINE = data_io.HOSPITAL_ADDY
JC_URL = ("https://www.qualitycheck.org/file.aspx?FolderName=" +
          "StrokeCertification&c=1")


def load_hospitals(hospital_file=MASTER_LIST_OFFLINE):
    '''
    Read in the given relative filepath as a table of hospital information
    '''
    if hospital_file is None: hospital_file = MASTER_LIST_OFFLINE
    hospitals = pd.read_csv(hospital_file, sep='|')
    if "HOSP_ID" in hospitals.columns:
        hospitals.set_index("HOSP_ID", inplace=True)
    return hospitals


def _save_master_list(data, savedir=MASTER_LIST_OFFLINE):
    data.to_csv(savedir, sep='|')


def master_list_online(update=False):
    '''
    Get the dataframe of all known hospitals, building it from Joint
        Commission certification if it doesn't exist, and optionally updating
        it to capture additions to the JC list.
    '''

    if MASTER_LIST.exists():
        existing = load_hospitals(MASTER_LIST)
    else:
        columns = [
            'CenterID', 'CenterType', 'OrganizationName', 'City', 'State',
            'PostalCode', 'Name', 'Address', 'Latitude', 'Longitude',
            'Failed_Lookup', 'destination', 'destinationID', 'transfer_time',
            'DTN_1st', 'DTN_Median', 'DTN_3rd', 'DTP_1st', 'DTP_Median',
            'DTP_3rd'
        ]
        existing = pd.DataFrame(columns=columns).set_index('CenterID')
        existing.Failed_Lookup = existing.Failed_Lookup.astype(bool)

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

        jc_data = jc_data.drop_duplicates(
            subset=['OrganizationId', 'City', 'State', 'PostalCode'])

        update_index = ['OrganizationName', 'City', 'State', 'PostalCode']
        jc_data = jc_data.set_index(update_index, verify_integrity=True)

        existing = existing.reset_index().set_index(update_index)

        new = jc_data[~jc_data.index.isin(existing.index)]
        new['Failed_Lookup'] = False
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
        _save_master_list(out, savedir=MASTER_LIST)
    else:
        out = existing

    return out


def update_locations(current=None):
    '''
    Use google maps to find addresses and coordinates for any hospitals that
        don't yet have them, meaning all of 'Name', 'Address', 'Latitude', and
        'Longitude' are NaN. If any of these are filled the hospital will be
        skipped. To perform manual updates directly edit `all.csv`; the
        function `maps.get_hospital_location` can be used to manually generate
        address and location from any search string.
    '''
    if current is None:
        current = load_hospitals()
        savedir = MASTER_LIST_OFFLINE
    else:
        savedir = current
        current = load_hospitals(current)

    loc_cols = ['Latitude', 'Longitude']
    no_data = current[loc_cols].isnull().all(axis=1)
    failed_lookup = np.where(current.Failed_Lookup.isnull(), False,
                             current.Failed_Lookup).astype(bool)
    to_update = current[no_data & ~failed_lookup].index

    if to_update.empty:
        print('No locations to update')
        return

    client = maps.get_client()
    for i in tqdm(to_update, desc='Getting Locations'):
        orgname = current.OrganizationName[i]
        address = current.Source_Address[i]
        if not isinstance(address, str):  # interpet nan type
            if str(address) == 'nan': address = ''
        city = current.City[i]
        state = current.State[i]
        postal = current.PostalCode[i]

        searchterm = ' '.join([orgname, address, city, state, postal])

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
        _save_master_list(current, savedir=savedir)


def update_transfer_destinations(data=None):
    '''
    Use google maps to find transfer destinations for all primary hospitals
        that don't yet have one stored. Doesn't overwrite any data.
    '''
    if data is None:
        data = load_hospitals()
        savedir = MASTER_LIST_OFFLINE
    else:
        savedir = data
        data = load_hospitals(data)

    # only calculate info for hospitals we dont have data for yet
    no_destination = data[['destination', 'destinationID',
                           'transfer_time']].isnull().any(axis=1)
    # Only consider hospitals with location information
    has_data = ~data[['Latitude', 'Longitude']].isnull().any(axis=1)
    to_update = data.loc[has_data & no_destination, :]

    prim_to_update = to_update[to_update.CenterType == 'Primary']
    if prim_to_update.empty:
        print('No primaries to find transfer destinations for')
        return

    comp_data = data[data.CenterType == 'Comprehensive']
    prim_locs = geo.extract_locations(prim_to_update)
    comp_locs = geo.extract_locations(comp_data)
    distances = geo.distance_matrix(prim_locs, comp_locs, prim_to_update.index,
                                    comp_data.index)

    client = maps.get_client()
    for i in tqdm(prim_to_update.index):
        comps = distances.loc[i]
        include = comps[comps < comps.Cutoff]
        prim_loc = geo.extract_locations(prim_to_update.loc[[i]])
        comp_locs = geo.extract_locations(comp_data.loc[include.index])

        results = maps.get_transfer_destination(prim_loc, comp_locs, client)

        if not results:
            name = prim_to_update.Name[i]
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
        _save_master_list(data, savedir=savedir)
