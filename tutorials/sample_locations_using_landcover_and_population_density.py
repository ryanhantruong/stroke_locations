import rasterio
import numpy as np
import shapely.geometry as shgeo
import rasterio.transform as rtransform
import rasterio.warp as rwarp
import rasterio.mask as rmask
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import plotly.offline as py
import data_io
from tools import MAPBOX_TOKEN


def crop_raster_from_geom(geoms):
    imgs = []
    transforms = []
    bids = []
    for bid, bg in geoms.iteritems():
        out_img, out_transform = rmask.mask(dataset=src,
                                            shapes=[bg],
                                            crop=True)
        imgs.append(out_img[0])
        transforms.append(out_transform)
        bids.append(bid)
    return bids, imgs, transforms


def sample_from_inhabitable_area(img, transform, sample_size=1):
    # Get inhabitable areas , developed area code starts from 21 to 31
    # Source: https://www.usgs.gov/centers/eros/science/
    #national-land-cover-database?qt-science_center_objects=0
    ##qt-science_center_objects
    amask = (img >= 21) & (img <= 31)
    goodr, goodc = np.nonzero(amask)

    # Get random locations sampling from goodr,goodc
    r_choices = np.random.choice(np.arange(goodr.size), size=sample_size)
    rs, cs = goodr[r_choices], goodc[r_choices]

    # Translate back into north america coordinates which is EPSG4269'EPSG:4269
    xs, ys = rtransform.xy(transform=transform, rows=rs, cols=cs)
    lons, lats = rwarp.transform(src.crs, block_groups.crs, xs, ys)
    return lons, lats


state_fip = '25'
src = rasterio.open(f'census_data/land_coverage/state{state_fip}.tif')
array = src.read(1)

# devleoped openspace is 21 which are just roads

# Get blockgroup shapes and population counts
gdf = gpd.read_file('census_data/tl_2018_MA_bg/tl_2018_25_bg.shp')
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

# Get subcounty shapes
gdf3 = gpd.read_file('census_data/tl_2018_25_cousub/tl_2018_25_cousub.shp')
gdf3 = gdf3[gdf3.ALAND > 0]  # remove blocks only have water

# Bin blockgroups into subcounties
subcounty_bg_list = []
for isub, subcounty in gdf3.iterrows():
    same_county = block_groups.loc[
        (block_groups.STATEFP == subcounty.STATEFP)
        & (block_groups.COUNTYFP == subcounty.COUNTYFP)]
    intersect_bg_geoids = []
    inters = []
    for i, bg in same_county.iterrows():
        if bg.geometry.intersects(subcounty.geometry):
            # print(f'intersect with blockgroup {bg.NAMELSAD}')
            inter = bg.geometry.intersection(subcounty.geometry)
            if type(inter) == shgeo.Polygon:
                intersect_bg_geoids.append(bg.GEOID)
                inters.append(inter)
    if len(intersect_bg_geoids) > 0:
        interdf = pd.DataFrame.from_dict({
            'GEOID': intersect_bg_geoids,
            'geometry': inters
        })
        interdf = interdf.merge(
            block_groups.loc[:, block_groups.columns != 'geometry'])
        nbgs = interdf.shape[0]
        prefix_df = pd.concat([subcounty.to_frame().T] *
                              nbgs).reset_index(drop=True)
        interdf.columns = interdf.columns.to_series().apply(
            lambda x: x + '_BlockGroup')
        subcounty_bg = pd.concat([prefix_df, interdf], axis=1)
        subcounty_bg_list.append(subcounty_bg)
bg_in_subcounty = pd.concat(subcounty_bg_list, ignore_index=True)

subcounty_geoids = []
# Choose a subcounty to use
subcounty_geoid = '2502338855'
subcounty_geoids.append(subcounty_geoid)

# Sampling
bg_cols = bg_in_subcounty.columns[
    bg_in_subcounty.columns.str.find('_BlockGroup') > -1]
bgs_sample_pool = bg_in_subcounty.loc[bg_in_subcounty.GEOID ==
                                      subcounty_geoid, bg_cols].rename(
                                          mapper=lambda x: x.replace(
                                              '_BlockGroup', ''),
                                          axis=1)
sampled_bgs = bgs_sample_pool.sample(n=50,
                                     weights='over_60',
                                     axis=0,
                                     replace=True).reset_index(drop=True)
sampled_bgs = gpd.GeoDataFrame(sampled_bgs, crs=block_groups.crs)

sampled_geoms = sampled_bgs['geometry'].to_crs(crs=src.crs)

bids, imgs, transforms = crop_raster_from_geom(sampled_geoms)
points = {
    bid: sample_from_inhabitable_area(img, transform)
    for bid, img, transform in zip(bids, imgs, transforms)
}
# unpack list since we have only sample 1 point
points = {k: (v[0][0], v[1][0]) for k, v in points.items()}
# convert to shapely points
spoints = {k: shgeo.Point(*v) for k, v in points.items()}
# put back into df
sampled_bgs = sampled_bgs.assign(
    Sampled_Point_Longitude=[p.x for p in spoints.values()],
    Sampled_Point_Latitude=[p.y for p in spoints.values()])
map_center = {
    "lat": sampled_bgs.Sampled_Point_Latitude.mean(),
    "lon": sampled_bgs.Sampled_Point_Longitude.mean()
}

# Sample again for boston city
# Choose a subcounty to use
subcounty_geoid = gdf3.loc[gdf3.NAMELSAD == 'Boston city', 'GEOID'].values[0]
subcounty_geoids.append(subcounty_geoid)
# Sampling
bg_cols = bg_in_subcounty.columns[
    bg_in_subcounty.columns.str.find('_BlockGroup') > -1]
bgs_sample_pool = bg_in_subcounty.loc[bg_in_subcounty.GEOID ==
                                      subcounty_geoid, bg_cols].rename(
                                          mapper=lambda x: x.replace(
                                              '_BlockGroup', ''),
                                          axis=1)
sampled_bgs_boston = bgs_sample_pool.sample(
    n=50, weights='over_60', axis=0, replace=True).reset_index(drop=True)
sampled_bgs_boston = gpd.GeoDataFrame(sampled_bgs_boston, crs=block_groups.crs)

sampled_geoms = sampled_bgs_boston['geometry'].to_crs(crs=src.crs)

bids, imgs, transforms = crop_raster_from_geom(sampled_geoms)
points = {
    bid: sample_from_inhabitable_area(img, transform)
    for bid, img, transform in zip(bids, imgs, transforms)
}
# unpack list since we have only sample 1 point
points = {k: (v[0][0], v[1][0]) for k, v in points.items()}
# convert to shapely points
spoints = {k: shgeo.Point(*v) for k, v in points.items()}
# put back into df
sampled_bgs_boston = sampled_bgs_boston.assign(
    Sampled_Point_Longitude=[p.x for p in spoints.values()],
    Sampled_Point_Latitude=[p.y for p in spoints.values()])

# Gather diff subcounty sampled poitns
sampled_bgs = pd.concat([sampled_bgs, sampled_bgs_boston], ignore_index=True)

# Start of plotting
subcounty_cols = bg_in_subcounty.columns[bg_in_subcounty.columns.str.find(
    '_BlockGroup') == -1]
choropleth_subcounty = gpd.GeoDataFrame(
    bg_in_subcounty.loc[bg_in_subcounty.GEOID.isin(subcounty_geoids
                                                   ), subcounty_cols])
bg_cols = bg_in_subcounty.columns[
    bg_in_subcounty.columns.str.find('_BlockGroup') > -1]
choropleth_bg = gpd.GeoDataFrame(
    bg_in_subcounty.loc[bg_in_subcounty.GEOID.isin(subcounty_geoids), bg_cols].
    rename(mapper=lambda x: x.replace('_BlockGroup', ''), axis=1))
hospitals = pd.read_csv(data_io.DTN_PATH /
                        'hospital_address_NE_for_stroke_locations.csv',
                        sep='|')
comprehensives = hospitals.loc[hospitals.CenterType == 'Comprehensive', :]
primaries = hospitals.loc[hospitals.CenterType != 'Comprehensive', :]

fig = go.Figure([
    go.Choroplethmapbox(
        geojson=choropleth_subcounty.set_index('GEOID').__geo_interface__,
        locations=choropleth_subcounty.GEOID,
        z=np.random.rand(choropleth_subcounty.shape[0]),
        text=choropleth_subcounty.NAMELSAD,
        hoverinfo="text",
        colorscale="Blackbody",
        marker_opacity=0.1,
        marker_line_width=5,
        marker_line_color="rgb(0,0,0)",
        showscale=False),
    go.Choroplethmapbox(
        geojson=choropleth_bg.set_index('GEOID').__geo_interface__,
        locations=choropleth_bg.GEOID,
        z=choropleth_bg.over_60,
        text=choropleth_bg.NAMELSAD,
        hoverinfo="text+z",
        colorscale="Viridis",
        marker_opacity=0.3,
        marker_line_width=2,
        marker_line_color="#C6C6C6"),
    go.Scattermapbox(lat=sampled_bgs.Sampled_Point_Latitude,
                     lon=sampled_bgs.Sampled_Point_Longitude,
                     mode='markers',
                     name='Patient Location',
                     marker=go.scattermapbox.Marker(color='rgb(0,0,0)')),
    go.Scattermapbox(lat=comprehensives.Latitude,
                     lon=comprehensives.Longitude,
                     name='Comprehensive',
                     text=comprehensives.OrganizationName,
                     hoverinfo='text',
                     mode='markers',
                     marker=go.scattermapbox.Marker(size=15,
                                                    color='rgb(255,0,0)')),
    go.Scattermapbox(lat=primaries.Latitude,
                     lon=primaries.Longitude,
                     text=primaries.OrganizationName,
                     hoverinfo='text',
                     name='Primary',
                     mode='markers',
                     marker=go.scattermapbox.Marker(size=15,
                                                    color='rgb(0,0,255)'))
])
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_accesstoken=MAPBOX_TOKEN,
                  mapbox_zoom=12,
                  mapbox_center=map_center)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.update_layout(legend=go.layout.Legend(x=0,
                                          y=1,
                                          traceorder="normal",
                                          font=dict(size=12, color="black"),
                                          bgcolor="White",
                                          bordercolor="Blue",
                                          borderwidth=2))

py.plot(fig, filename='subcounties_w_landcover_n=50.html')

sampled_bgs.to_csv('data/points/Marshfield_town_MA_fulldetails_n=50.csv',
                   index=False)

for_model = sampled_bgs[['Sampled_Point_Latitude',
                         'Sampled_Point_Longitude']].reset_index()
for_model.columns = ['LOC_ID', 'Latitude', 'Longitude']
for_model.LOC_ID = for_model.LOC_ID.apply(lambda x: 'L' + str(x))
for_model.to_csv('data/points/Marshfield_town_MA_n=50.csv', index=False)
