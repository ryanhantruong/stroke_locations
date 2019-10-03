import pandas as pd
import urllib.request as ur
import urllib.parse as up
import json
import data_io
from tools import MAPBOX_TOKEN

addy_path = data_io.DTN_PATH / f'hospital_address_NE_for_stroke_locations.csv'

df = pd.read_csv(addy_path, sep='|')


def get_best_result(results):
    results.place_type = results.place_type.apply(lambda x: x[0])
    type_m = results.place_type.isin(['address', 'poi'])
    results = results[type_m]
    results.loc[results.place_type == 'poi', 'relevance'] += .1
    results.sort_values(['relevance'], ascending=False, inplace=True)
    if results.empty: return None
    return results.iloc[0, :]


contextl = []
for idf, row in df.iterrows():
    for_join = pd.Series([
        row.OrganizationName, row.Source_Address, row.City, row.State,
        row.PostalCode
    ]).dropna().values
    if len(for_join) == 0: continue
    quote_address = up.quote_plus(' '.join(for_join))
    print(quote_address)
    mapbox_query = f'https://api.mapbox.com/geocoding/v5/mapbox.places/'\
    +f'{quote_address}.json?access_token={MAPBOX_TOKEN}'
    response = ur.urlopen(mapbox_query)
    out = json.loads(response.read())
    results = pd.DataFrame.from_dict(out['features'])
    best_result = get_best_result(results)
    if best_result is None: continue
    lon, lat = best_result.center
    context = pd.DataFrame.from_dict(best_result.context)[['id', 'text']]
    context.id = context.id.apply(lambda x: x.split('.')[0])
    context = context.set_index('id').T
    properties = pd.DataFrame.from_dict(best_result.properties,
                                        orient='index').T
    name = best_result.text
    full_name = best_result.place_name
    result_parsed = context.reset_index(drop=True).join(
        properties.reset_index(drop=True))
    result_parsed = result_parsed.assign(name=name,
                                         full_name=full_name,
                                         longitude=lon,
                                         latitude=lat)
    result_parsed.index = [idf]
    contextl.append(result_parsed)

all_results = pd.concat(contextl)

df[df.columns[:6]].join(all_results, how='outer').to_excel(
    'hospital_address_NE_for_stroke_locations_mapbox_search.xlsx', index=False)

# put into original address list
mapbox = pd.read_excel(
    data_io.DTN_PATH /
    'hospital_address_NE_for_stroke_locations_mapbox_search.xlsx')
success_m = (mapbox.category.str.find('hospital') >
             -1) | (mapbox.category.str.find('emergency') >
                    -1) | (mapbox.category.str.find('medical center') > -1)
mapbox_hospitals = mapbox.loc[
    success_m, ['HOSP_ID', 'name', 'full_name', 'latitude', 'longitude']]

mapbox_hospitals['full_address'] = mapbox_hospitals.full_name.apply(
    lambda x: ','.join(x.split(',')[1:]))
mapbox_hospitals.drop('full_name', axis=1, inplace=True)
mapbox_hospitals.columns = [
    'HOSP_ID', 'Name', 'Latitude', 'Longitude', 'Address'
]

# update info into original DF
to_fillin_df = pd.read_csv(data_io.DTN_PATH /
                           'hospital_address_NE_for_stroke_locations.csv',
                           sep='|',
                           dtype=str,
                           index_col=[0])
to_fillin_df.update(mapbox_hospitals.set_index('HOSP_ID'), overwrite=False)
failed_lookup = to_fillin_df[['Latitude', 'Longitude']].isna().any(axis=1)
failed_lookup = failed_lookup[~failed_lookup]
to_fillin_df.Failed_Lookup.update(failed_lookup)

to_fillin_df.to_csv(data_io.DTN_PATH /
                    'hospital_address_NE_for_stroke_locations.csv',
                    sep='|')
#Review
to_fillin_df = pd.read_csv(data_io.DTN_PATH /
                           'hospital_address_NE_for_stroke_locations.csv',
                           sep='|',
                           dtype=str,
                           index_col=[0])

# Run google map search service
# import hospitals
# hospitals.update_locations(data_io.DTN_PATH /'hospital_address_NE_for_stroke_locations.csv',)

# Manual update one entry
manual_update = {
    'HOSP_ID': ['ID6142130A', 'ID6290O', 'ID4408O', 'ID6210393A'],
    'Name': [
        'Harrington HealthCare at Hubbard',
        'MedStar Montgomery Medical Center',
        'St. Luke\'s Hospital - Miners Campus',
        'Montefiore Medical Center: Einstein Campus'
    ],
    'Address': [
        '340 Thompson Rd, Webster, MA 01570',
        '18101 Prince Philip Dr, Olney, MD 20832',
        '360 W Ruddle St, Coaldale, PA 18218',
        '1825 Eastchester Rd, The Bronx, NY 10461'
    ],
    'Latitude': [42.027325, 39.153826, 40.821270, 40.849209],
    'Longitude': [-71.851023, -77.055229, -75.914550, -73.845839],
    'Failed_Lookup': [False, False, False, False]
}

to_fillin_df.update(pd.DataFrame.from_dict(manual_update).set_index("HOSP_ID"))
to_fillin_df.to_csv(data_io.DTN_PATH /
                    'hospital_address_NE_for_stroke_locations.csv',
                    sep='|')
to_fillin_df.to_excel(
    data_io.DTN_PATH /
    'hospital_address_NE_for_stroke_locations_for_viewing.xlsx')
