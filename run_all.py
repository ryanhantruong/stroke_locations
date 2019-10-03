import hospitals
import population
import travel_times as times
import anonymize
import data_io
''' Run on all methods need to generate inputs for Stroke model '''

# Generate patient locations
# nsample locs across all X states, not nsample locs per state
states = ['NY', 'MA', 'NJ', 'CT', 'NH', 'RI', 'ME', 'VT']
nsample = 100
population.generate_points(states=states, n=nsample)

addy_path = data_io.DTN_PATH / f'hospital_address_NE_for_stroke_locations.csv'

# Careful
# Require Google Maps usage so can be $$$ for lots of location
hospitals.update_locations(addy_path)
hospitals.update_transfer_destinations(addy_path)

# Careful
# Need Gmaps, expensive operation
states_str = '_'.join(states)
times.get_travel_times(point_file=f'data\points\{states_str}_n={nsample}.csv',
                       allow_large=True,
                       hospital_address=addy_path)
times.get_travel_times(point_file=f'data\points\{states_str}_n={nsample}.csv',
                       allow_large=True,
                       hospital_address=addy_path)

# Remove identifiers from data
key_path = data_io.DTN_PATH / f'hospital_keys_master_v2.csv'
anonymize.prepare(time_file=f'data/travel_times/{states_str}_n={nsample}.csv',
                  hospital_address=addy_path,
                  hospital_key=key_path)

# Check in output/points and output/times for output
# Feed these csvs into stroke model
