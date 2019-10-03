import plotly.graph_objects as go
import plotly.offline as py
import data_io
import pandas as pd
from pathlib import Path
import tools
import argparse


def draw(points_p='data/points/NY_n=10000.csv',
         hospitals_p=data_io.DTN_PATH /
         'hospital_address_NE_for_stroke_locations.csv'):
    filepath = Path(points_p)
    sampled_bgs = pd.read_csv(filepath)
    map_center = {
        "lat": sampled_bgs.Latitude.mean(),
        "lon": sampled_bgs.Longitude.mean()
    }

    hospitals = pd.read_csv(hospitals_p, sep='|')
    comprehensives = hospitals.loc[hospitals.CenterType == 'Comprehensive', :]
    primaries = hospitals.loc[hospitals.CenterType != 'Comprehensive', :]

    fig = go.Figure([
        go.Scattermapbox(lat=sampled_bgs.Latitude,
                         lon=sampled_bgs.Longitude,
                         text=sampled_bgs.LOC_ID,
                         hoverinfo='text',
                         mode='markers',
                         name='Patient Location',
                         marker=go.scattermapbox.Marker(color='rgb(0,0,0)')),
        go.Scattermapbox(lat=comprehensives.Latitude,
                         lon=comprehensives.Longitude,
                         name='Comprehensive',
                         text=comprehensives.Name,
                         hoverinfo='text',
                         mode='markers',
                         marker=go.scattermapbox.Marker(size=15,
                                                        color='rgb(255,0,0)')),
        go.Scattermapbox(lat=primaries.Latitude,
                         lon=primaries.Longitude,
                         text=primaries.Name,
                         hoverinfo='text',
                         name='Primary',
                         mode='markers',
                         marker=go.scattermapbox.Marker(size=15,
                                                        color='rgb(0,0,255)'))
    ])
    fig.update_layout(mapbox_style="carto-positron",
                      mapbox_accesstoken=tools.MAPBOX_TOKEN,
                      mapbox_zoom=8,
                      mapbox_center=map_center)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(
        legend=go.layout.Legend(x=0,
                                y=1,
                                traceorder="normal",
                                font=dict(size=12, color="black"),
                                bgcolor="White",
                                bordercolor="Blue",
                                borderwidth=2))
    py.plot(fig, filename=f'output/maps/{filepath.stem}.html')


def main(args):
    hospital_file = args.hospital_file
    if hospital_file is None:
        hospital_file = data_io.DTN_PATH / 'hospital_address_NE_for_stroke_locations.csv'
    point_file = args.point_file
    draw(point_file, hospital_file)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('point_file', help='Path to locations to plot')
    parser.add_argument('hospital_file',
                        help='Path to hospitals to plot (optional)',
                        default=None,
                        nargs='?')
    args = parser.parse_args()
    main(args)
