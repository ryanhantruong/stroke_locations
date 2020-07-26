import hospitals
import population
import travel_times as times
import anonymize
import data_io
''' Run on all methods need to generate inputs for Stroke model '''

# Preparation:
# follow curate_census_data.py manual instructions and execute script
# OR use premade census data in census_data/SF2010/*.csv

# Generate patient locations
# nsample locs across all X states, not nsample locs per state
states = ['NY', 'MA', 'NJ', 'CT', 'NH', 'RI', 'ME', 'VT']
nsample = 10000
states_str = '_'.join(states)
population.generate_points(states=states, n=nsample)
# will create csv in 'data\points\{states_str}_n={nsample}.csv'

addy_path = data_io.DTN_PATH / f'hospital_address_NE_for_stroke_locations.csv'
# Careful
# Require Google Maps usage so can be $$$ for lots of location
hospitals.update_locations(addy_path)
hospitals.update_transfer_destinations(addy_path)
# will update existing csv specified by addy_path

# Careful
# Need Gmaps, expensive operation
times.get_travel_times(point_file=f'data/points/{states_str}_n={nsample}.csv',
                       allow_large=True,
                       hospital_address=addy_path)
# will create csv in 'data\travel_times\{states_str}_n={nsample}.csv'

# Remove identifiers from data
key_path = data_io.DTN_PATH / f'hospital_keys_master_v2.csv'
anonymize.prepare(time_file=f'data/travel_times/{states_str}_n={nsample}.csv',
                  hospital_address=addy_path,
                  hospital_key=key_path)
# Will create csv in output/hospitals and output/times
# Used these csv as inputs for stroke model
