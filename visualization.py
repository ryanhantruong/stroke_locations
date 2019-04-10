'''Generate visualizations of points and hospitals'''
import os
import argparse
import pandas as pd
import gmplot
import hospitals
import maps
import tools

MAP_DIR = os.path.join('output', 'maps')
if not os.path.isdir(MAP_DIR):
    os.makedirs(MAP_DIR)


def _get_lats_and_longs(data):
    '''Convert locations to form gmplot expects'''
    lats = []
    longs = []
    for i in data.index:
        lats.append(data.Latitude[i])
        longs.append(data.Longitude[i])

    return lats, longs


def _get_middle(series):
    '''Get a value halfway from the max to the min'''
    max_ = series.max()
    min_ = series.min()
    return (max_ + min_) / 2


def create_map(points, centers, name, center=None, zoom=7, heatmap=True):
    '''
    Create a heatmap of the given points, with markers for stroke centers.
        All data should be passed as dataframes with Latitude and Longitude
        name -- custom name to use in output file
        center -- custom location to center the map, defaults to midpoint
    '''
    if center is None:
        mid_lat = _get_middle(points.Latitude)
        mid_long = _get_middle(points.Longitude)
    else:
        mid_lat, mid_long = center

    plotter = gmplot.GoogleMapPlotter(mid_lat, mid_long, zoom, maps.get_key())
    lats, longs = _get_lats_and_longs(points)
    if heatmap:
        plotter.heatmap(lats, longs, dissipating=True)
    else:
        plotter.scatter(lats, longs, marker=False, color='green', size=200)

    if centers is not None:
        primaries = centers[centers.CenterType == 'Primary']
        prim_lats, prim_longs = _get_lats_and_longs(primaries)
        plotter.scatter(prim_lats, prim_longs, color='red', marker=True)

        comprehensives = centers[centers.CenterType == 'Comprehensive']
        comp_lats, comp_longs = _get_lats_and_longs(comprehensives)
        plotter.scatter(comp_lats, comp_longs, color='blue', marker=True)

    if heatmap:
        name += '_heatmap'
    plotter.draw(os.path.join(MAP_DIR, f'{name}.html'))


def main(args):
    '''Create a heatmap for given input files'''
    hospital_file = args.hospital_file
    point_file = args.point_file
    heatmap = args.heatmap

    if hospital_file is None:
        centers = None
        hosp_name = 'None'
    else:
        try:
            # load the hospital file with latitude and longtitude
            # not de-identified yet
            centers = hospitals.load_hospitals_han(hospital_file)
        except KeyError:
            # hospital_file is comma-separated anonymized file
            # centers = pd.read_csv(hospital_file).set_index('CenterID')
            centers = pd.read_csv(hospital_file,index_col=0)
        all_hosps = hospitals.master_list_offline()
        all_hosps.set_index('AHA_ID',inplace=True)
        if centers.index.name == 'HOSP_KEY':
            # reindex all_hosps into HOSP_KEY
            all_hosps.index = all_hosps.index.map(tools.get_hosp_keys())
        centers = all_hosps[all_hosps.index.isin(centers.index)]
        hosp_name = os.path.basename(hospital_file).strip('.csv')

    points = pd.read_csv(point_file)
    point_name = os.path.basename(point_file).strip('.csv')
    if 'Latitude' not in points:
        # point_file is anonymized, look for its source
        try:
            points = pd.read_csv(os.path.join('data', 'points',
                                              point_name + '.csv'))
        except FileNotFoundError:
            points = None

        if points is None:
            msg = "Couldn't find locations for anonymous points"
            msg += f" in {point_file}"
            raise ValueError(msg)

    if point_name == hosp_name:
        name = point_name
    else:
        name = f'{point_name}_{hosp_name}'

    create_map(points, centers, name, heatmap=heatmap)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('point_file', help='Path to locations to plot')
    parser.add_argument('hospital_file',
                        help='Path to hospitals to plot (optional)',
                        default=None, nargs='?')
    parser.add_argument('--heatmap', '--heat', action='store_true',
                        help='Generate a heatmap rather than points')
    args = parser.parse_args()
    main(args)
