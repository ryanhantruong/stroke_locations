import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as py
import numpy as np
import shapely.geometry as sh_geo
from tools import MAPBOX_TOKEN


def _get_random_point_in_polygon(poly):
    '''From https://gis.stackexchange.com/a/6413'''
    (minx, miny, maxx, maxy) = poly.bounds
    while True:
        p = sh_geo.Point(np.random.uniform(minx, maxx),
                         np.random.uniform(miny, maxy))
        if poly.contains(p):
            return p


def _get_polygon_center(poly):
    '''From https://gis.stackexchange.com/a/6413'''
    (minx, miny, maxx, maxy) = poly.bounds
    p = sh_geo.Point(minx + ((maxx - minx) / 2), miny + ((maxy - miny) / 2))
    if poly.contains(p):
        return p
    else:
        return _get_random_point_in_polygon(poly)


gdf = gpd.read_file('census_data/tl_2018_MA_bg/tl_2018_25_bg.shp')
# gdf2 = gpd.read_file('census_data/tl_2018_36_tract/tl_2018_36_tract.shp')
gdf3 = gpd.read_file('census_data/tl_2018_25_cousub/tl_2018_25_cousub.shp')
gdf3 = gdf3[gdf3.ALAND > 0]  # remove blocks only have water
dff = pd.read_csv(
    'census_data/ACS_17_MA_sex_by_age_all_block_groups/ACS_17_5YR_B01001_with_ann.csv',
    skiprows=[1],
    dtype=str)
dff.iloc[:, 3:] = dff.iloc[:, 3:].astype(int)
male_count_columns = [f'HD01_VD{str(x).zfill(2)}' for x in range(18, 26)]
female_count_columns = [f'HD01_VD{str(x).zfill(2)}' for x in range(42, 50)]
dff['over_60'] = dff[male_count_columns + female_count_columns].sum(axis=1)
dff['total'] = dff['HD01_VD01']
dff['GEOID'] = dff['GEO.id2']
mdf = gdf.merge(dff[['GEOID', 'over_60', 'total']])
mdf = mdf[mdf.ALAND > 0]  # remove blocks only have water

block_groups = mdf.drop(['geometry'], axis=1)
block_groups = block_groups[block_groups.over_60 > 0]
block_groups = gdf[['GEOID', 'geometry']].merge(block_groups, on='GEOID')


def convert_to_shapely_point(df):
    # INTPTLAT & INTLON are center of block groups
    return gpd.GeoDataFrame(geometry=[
        sh_geo.Point(float(row.loc['INTPTLON']), float(row.loc['INTPTLAT']))
        for index, row in df.iterrows()
    ],
                            index=df.index)


bg_points = convert_to_shapely_point(block_groups)
out = {
    key: row.GEOID
    for key2, row in gdf3.iterrows() for key, pt in bg_points.geometry.items()
    if pt.within(row.geometry)
}
block_groups['cousub_GEOID'] = pd.Series(out)
block_groups


def get_n_max(df, population_count_col, n=3):
    return df.sort_values(population_count_col).iloc[-n:]


largest_blocks = block_groups.groupby('cousub_GEOID').apply(
    get_n_max, population_count_col='over_60', n=10)
# largest_blocks.shape
# largest_blocks = block_groups

NY_CENTER = {"lat": 40.7831, "lon": -73.9712}
BOSTON_CENTER = {"lat": 42.3601, "lon": -71.0589}

fig = go.Figure([
    go.Choroplethmapbox(geojson=gdf3.set_index('GEOID').__geo_interface__,
                        locations=gdf3.GEOID,
                        z=np.random.rand(gdf3.shape[0]),
                        text=gdf3.NAMELSAD,
                        hoverinfo="location+text+z",
                        colorscale="Viridis",
                        marker_opacity=0.5,
                        marker_line_width=2,
                        marker_line_color="#C6C6C6"),
    go.Scattermapbox(lat=largest_blocks.INTPTLAT.astype(float),
                     lon=largest_blocks.INTPTLON.astype(float),
                     text=largest_blocks.GEOID + '\n' +
                     largest_blocks.NAMELSAD + '\n' +
                     largest_blocks.over_60.astype(str),
                     hoverinfo="text",
                     mode='markers',
                     marker=go.scattermapbox.Marker(size=10,
                                                    color='rgb(220,220,220)'))
])
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_accesstoken=MAPBOX_TOKEN,
                  mapbox_zoom=12,
                  mapbox_center=BOSTON_CENTER)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

py.plot(fig, filename='MA_cousub_center_over60_population_bgs.html')

want_list = ['Boston city', 'Wellesley town', 'Athol town']
geoids = {k: gdf3.loc[gdf3.NAMELSAD == k, 'GEOID'].iloc[0] for k in want_list}

to_save = largest_blocks.loc[geoids['Boston city']][[
    'GEOID', 'INTPTLAT', 'INTPTLON'
]]
to_save.columns = ['LOC_ID', 'Latitude', 'Longitude']
to_save.LOC_ID = to_save.LOC_ID.apply(lambda x: 'L' + x)
to_save.to_csv('data/points/Boston_city_n=10.csv', index=False)

to_save = largest_blocks.loc[geoids['Wellesley town']][[
    'GEOID', 'INTPTLAT', 'INTPTLON'
]]
to_save.columns = ['LOC_ID', 'Latitude', 'Longitude']
to_save.LOC_ID = to_save.LOC_ID.apply(lambda x: 'L' + x)
to_save.to_csv('data/points/Wellesley_town_n=10.csv', index=False)

sampled_points = gdf3.loc[gdf3.NAMELSAD == 'Athol town', 'geometry'].repeat(
    2).apply(_get_random_point_in_polygon)
sampled_points = pd.DataFrame().assign(
    LOC_ID=['LRAND1', 'LRAND2'],
    Latitude=sampled_points.apply(lambda p: p.y).astype(str).values,
    Longitude=sampled_points.apply(lambda p: p.x).astype(str).values)

to_save = largest_blocks.loc[geoids['Athol town']][[
    'GEOID', 'INTPTLAT', 'INTPTLON'
]]
to_save.columns = ['LOC_ID', 'Latitude', 'Longitude']
to_save.LOC_ID = to_save.LOC_ID.apply(lambda x: 'L' + x)
to_save = to_save.append(sampled_points)
to_save.to_csv('data/points/Athol_town_n=10.csv', index=False)

choropleth = gdf3.loc[gdf3.NAMELSAD == 'Athol town', :]
fig = go.Figure([
    go.Choroplethmapbox(
        geojson=choropleth.set_index('GEOID').__geo_interface__,
        locations=choropleth.GEOID,
        z=np.random.rand(choropleth.shape[0]),
        text=choropleth.NAMELSAD,
        hoverinfo="location+text+z",
        colorscale="Viridis",
        marker_opacity=0.5,
        marker_line_width=2,
        marker_line_color="#C6C6C6"),
    go.Scattermapbox(lat=to_save.Latitude.astype(float),
                     lon=to_save.Longitude.astype(float),
                     text=to_save.LOC_ID,
                     hoverinfo="text",
                     mode='markers',
                     marker=go.scattermapbox.Marker(size=10,
                                                    color='rgb(220,220,220)'))
])
map_center = {
    'lat': to_save.Latitude.astype(float).mean(),
    'lon': to_save.Longitude.astype(float).mean()
}
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_accesstoken=MAPBOX_TOKEN,
                  mapbox_zoom=12,
                  mapbox_center=map_center)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

py.plot(fig, filename='Athol_town_n=10.html')
