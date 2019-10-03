import geopandas as gpd
import plotly.graph_objects as go
import plotly.offline as py
import data_io
import numpy as np
import pandas as pd
from tools import MAPBOX_TOKEN

# Get subcounty shapes
gdf = gpd.read_file('census_data/tl_2018_25_cousub/tl_2018_25_cousub.shp')
gdf = gdf[gdf.ALAND > 0]  # remove blocks only have water

# Start of plotting
choropleth_subcounty = gdf

hospitals = pd.read_csv(data_io.DTN_PATH /
                        'strokecenter_address_MA_for_stroke_locations.csv',
                        sep='|')
comprehensives = hospitals.loc[hospitals.CenterType == 'Comprehensive', :]
primaries = hospitals.loc[hospitals.CenterType != 'Comprehensive', :]
map_center = {
    'lat': hospitals.Latitude.mean(),
    'lon': hospitals.Longitude.mean()
}

fig = go.Figure([
    go.Choroplethmapbox(
        geojson=choropleth_subcounty.set_index('GEOID').__geo_interface__,
        locations=choropleth_subcounty.GEOID,
        z=np.random.rand(choropleth_subcounty.shape[0]),
        text=choropleth_subcounty.NAMELSAD,
        hoverinfo="text",
        colorscale="Viridis",
        marker_opacity=0.15,
        marker_line_width=3,
        marker_line_color="rgb(0,0,0)",
        showscale=False),
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
                  mapbox_zoom=8,
                  mapbox_center=map_center)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.update_layout(legend=go.layout.Legend(x=0,
                                          y=1,
                                          traceorder="normal",
                                          font=dict(size=12, color="black"),
                                          bgcolor="White",
                                          bordercolor="Blue",
                                          borderwidth=2))

py.plot(fig, filename='output/maps/MA_subcounty_w_hospitals.html')
