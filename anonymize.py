'''Remove identifying information from hospital and travel time files'''
import os
import argparse
import pandas as pd
import hospitals
import travel_times
import data_io


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
    times = travel_times.read_travel_times(time_file)
    # Deidentify, drop columns that show locations/not needed
    times = times.drop(columns=['Latitude', 'Longitude','Need_Update'])
    hosp_ids = [x for x in times.columns]

    if hospital_address is None: hospital_address = data_io.HOSPITAL_ADDY
    all_hospitals = hospitals.load_hospitals(hospital_address)
    hosps = all_hospitals[all_hospitals.index.isin(hosp_ids)]
    if hosps.shape[0] == 0: raise ValueError('No hospitals found; check files')

    # deidentify AHA_ID into HOSP_KEY
    # if AHA_ID is not in dictionary's key, returns original AHA_ID
    if hospital_key is None: hosp_keys = data_io.get_hosp_keys()
    hosp_keys = data_io.get_hosp_keys(hospital_key)
    # Deidentify ID into key
    hosps.rename(hosp_keys,axis=0,inplace=True)
    hosps.index.name='HOSP_KEY'
    # Deidentify transfer destination ID to key
    hosps['destination_KEY']=hosps['destinationID'].map(hosp_keys,
                                                        na_action='ignore')
    # Only keep columns that are needed
    hosps = hosps[['CenterType','Source','transfer_time','destination_KEY']]

    # Deidentify the column names (HOSP_ID) in times
    times.columns = times.columns.map(hosp_keys)

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
