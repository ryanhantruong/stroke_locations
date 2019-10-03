'''Remove identifying information from hospital and travel time files'''
import os
import argparse
import pandas as pd
import hospitals
import tools

HOSPITALS_OUT = os.path.join('output', 'hospitals')
if not os.path.isdir(HOSPITALS_OUT):
    os.makedirs(HOSPITALS_OUT)

TIMES_OUT = os.path.join('output', 'travel_times')
if not os.path.isdir(TIMES_OUT):
    os.makedirs(TIMES_OUT)

def prepare(time_file,hospital_address=None,hospital_key=None):
    '''
    Generate travel times and hospital files for the given travel
        times file with identifying information removed.
    '''
    name = os.path.basename(time_file)
    times = pd.read_csv(time_file).set_index('LOC_ID')
    # Deidentify
    times = times.drop(columns=['Latitude', 'Longitude'])
    hosp_ids = [x for x in times.columns]

    if hospital_address is None:
        all_hospitals = hospitals.master_list_offline()
    else:
        all_hospitals = pd.read_csv(hospital_address,sep='|')
    all_hospitals.set_index('HOSP_ID',inplace=True)
    hosps = all_hospitals[all_hospitals.index.isin(hosp_ids)]

    hosp_count = hosps.shape[0]
    print(f'Found {hosp_count} hospitals')
    if hosp_count == 0:
        raise ValueError('No hospitals found; check files')

    # deidentify AHA_ID into HOSP_KEY
    # if AHA_ID is not in dictionary's key, returns original AHA_ID
    if hospital_key is None:
        hosp_keys = tools.get_hosp_keys()
    else:
        keys_df = pd.read_csv(hospital_key).set_index('HOSP_ID')
        hosp_keys = keys_df['HOSP_KEY'].to_dict()
    hosps.rename(hosp_keys,axis=0,inplace=True)
    hosps.index.name='HOSP_KEY'
    hosps['destination_KEY']=hosps['destinationID'].map(hosp_keys,na_action='ignore')
    # deidentify column names (HOSP_ID) in times
    times.columns = times.columns.map(hosp_keys)

    hosps = hosps.drop(
        columns=[
            'OrganizationName', 'City', 'State', 'PostalCode','Original_ID_Name',
            'AHA_ID','OrganizationId',
            'Name', 'Source_Address','Address', 'Failed_Lookup','destinationID',
            'Latitude', 'Longitude', 'destination',
        ]
    )

    times.to_csv(os.path.join(TIMES_OUT, name))
    hosps.to_csv(os.path.join(HOSPITALS_OUT, name))

def main(args):
    time_file = args.time_file
    prepare(time_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('time_file', help='Path to travel times')
    args = parser.parse_args()
    main(args)
