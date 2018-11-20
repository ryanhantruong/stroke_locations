'''Use census data to generate random points according to population density'''
import os
import pandas as pd
import numpy as np
import shapely.geometry as sh_geo
import census


NORTHEAST = [
    'Maine', 'Vermont', 'New Hampshire', 'Massachusetts',
    'Rhode Island', 'Connecticut', 'New York',
]


def generate_grid(states=['Connecticut'], n=1000, name=None):
    if name is None:
        name = '_'.join(states)
    data = census.read_states(states)
    grid = _get_points(data, n)

    grid.to_csv(os.path.join('data', 'points', f'{name}_n={n}.csv'),
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
