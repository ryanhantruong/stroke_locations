'''Remove identifying information from hospital and travel time files'''
import os
import argparse
import pandas as pd
import hospitals


HOSPITALS_OUT = os.path.join('output', 'hospitals')
if not os.path.isdir(HOSPITALS_OUT):
    os.makedirs(HOSPITALS_OUT)

TIMES_OUT = os.path.join('output', 'travel_times')
if not os.path.isdir(TIMES_OUT):
    os.makedirs(TIMES_OUT)


def prepare(time_file):
    '''
    Generate travel times and hospital files for the given travel
        times file with identifying information removed.
    '''
    name = os.path.basename(time_file)
    times = pd.read_csv(time_file)
    times = times.drop(columns=['Latitude', 'Longitude'])
    times.index.name = 'ID'
    hosp_ids = [int(x) for x in times.columns]

    all_hospitals = hospitals.master_list()
    hosps = all_hospitals[all_hospitals.index.isin(hosp_ids)]

    hosp_count = hosps.shape[0]
    print(f'Found {hosp_count} hospitals')
    if hosp_count == 0:
        raise ValueError('No hospitals found; check files')

    hosps = hosps.drop(
        columns=[
            'OrganizationName', 'City', 'State', 'PostalCode',
            'Name', 'Address', 'Failed_Lookup',
            'Latitude', 'Longitude', 'destination',
            'OrganizationId', 'Program',
            'CertificationProgram', 'CertificationDecision', 'EffectiveDate'
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
