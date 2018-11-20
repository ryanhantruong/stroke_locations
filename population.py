'''Use census data to generate random points according to population density'''
import os
import argparse
import pandas as pd
import numpy as np
import shapely.geometry as sh_geo
import census


POINTS_DIR = os.path.join('data', 'points')
if not os.path.isdir(POINTS_DIR):
    os.makedirs(POINTS_DIR)

NORTHEAST = [
    'Maine', 'Vermont', 'New Hampshire', 'Massachusetts',
    'Rhode Island', 'Connecticut', 'New York',
]


def generate_points(states=['Connecticut'], n=1000, name=None):
    '''
    Generate a set of points randomly distributed across the given states
        according to population density. Points are returned as a dataframe
        and saved to a csv, using the given name or the names of the states
    '''
    data, states = census.read_states(states)
    grid = _get_points(data, n)

    if name is None:
        name = '_'.join(states)

    grid.to_csv(os.path.join(POINTS_DIR, f'{name}_n={n}.csv'),
                index=False)
    return grid


def _get_random_point_in_polygon(poly):
    '''From https://gis.stackexchange.com/a/6413'''
    (minx, miny, maxx, maxy) = poly.bounds
    while True:
        p = sh_geo.Point(np.random.uniform(minx, maxx),
                         np.random.uniform(miny, maxy))
        if poly.contains(p):
            return p


def _get_points(data, n=1000):
    samp = data.sample(n, replace=True, weights='POP10')
    points = samp.geometry.apply(_get_random_point_in_polygon)
    out = pd.DataFrame({'Latitude': points.apply(lambda p: p.y),
                        'Longitude': points.apply(lambda p: p.x)})
    return out


def main(args):
    '''
    Generate a file with points as described by command line arguments
    '''
    states = args.state
    if not states:
        states = NORTHEAST
    n = args.points
    name = args.filename

    generate_points(states, n, name)


if __name__ == '__main__':
    n_default = 1000
    name_default = None

    parser = argparse.ArgumentParser()
    state_help = 'One or more states to include. Defaults to the Northeast.'
    parser.add_argument('state', nargs='*', help=state_help)
    n_help = f'Number of points to generate (default {n_default})'
    parser.add_argument('--points', '-p', type=int, default=n_default,
                        help=n_help)
    name_help = f'Name for the resulting file (defaults to state names)'
    parser.add_argument('--filename', '-f', default=name_default,
                        help=name_help)
    args = parser.parse_args()
    main(args)
