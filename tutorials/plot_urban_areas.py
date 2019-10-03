import geopandas as gpd
import plotly.graph_objects as go
import plotly.offline as py
import numpy as np
from tools import MAPBOX_TOKEN

gdf = gpd.read_file('census_data/tl_2018_25_tract/tl_2018_25_tract.shp')
gdf2 = gpd.read_file('census_data/tl_2018_urban_areas/tl_2018_us_uac10.shp')

gdf2['Type'] = gdf2.UATYP10.map({'U': 0, 'C': 1})

BOSTON_CENTER = {"lat": 42.3601, "lon": -71.0589}
fig = go.Figure([
    go.Choroplethmapbox(geojson=gdf.set_index('GEOID').__geo_interface__,
                        locations=gdf.GEOID,
                        z=np.random.rand(gdf.shape[0]),
                        text=gdf.NAMELSAD,
                        hoverinfo="location+text",
                        colorscale="Viridis",
                        marker_opacity=0.5,
                        marker_line_width=2,
                        marker_line_color="#C6C6C6"),
    go.Choroplethmapbox(geojson=gdf2.set_index('GEOID10').__geo_interface__,
                        locations=gdf2.GEOID10,
                        z=gdf2.Type,
                        text=gdf2.NAMELSAD10,
                        hoverinfo="text+z",
                        colorscale="Magma",
                        marker_opacity=0.2,
                        marker_line_width=2,
                        marker_line_color="#C6C6C6")
])
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_accesstoken=MAPBOX_TOKEN,
                  mapbox_zoom=12,
                  mapbox_center=BOSTON_CENTER)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

py.plot(fig, filename='urban_area_over_tract.html')

gdf2.shape
BOSTON_CENTER = {"lat": 42.3601, "lon": -71.0589}
fig = go.Figure([
    go.Choroplethmapbox(geojson=gdf2.set_index('GEOID10').__geo_interface__,
                        locations=gdf2.GEOID10,
                        z=gdf2.Type,
                        text=gdf2.NAMELSAD10,
                        hoverinfo="text+z",
                        colorscale="Magma",
                        marker_opacity=0.2,
                        marker_line_width=2,
                        marker_line_color="#C6C6C6")
])
fig.update_layout(mapbox_style="carto-positron",
                  mapbox_accesstoken=MAPBOX_TOKEN,
                  mapbox_zoom=12,
                  mapbox_center=BOSTON_CENTER)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

py.plot(fig, filename='urban_areas.html')
