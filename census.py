'''Download and read population files from the 2010 census.'''
import os
import pandas as pd
import geopandas as gpd


def read_states(states=['Connecticut']):
    dirs = [os.path.join('data', 'census', st) for st in states]
    files = []
    for d in dirs:
        for f in os.listdir(d):
            if f.endswith('.shp'):
                files.append(os.path.join(d, f))
    sub_dfs = [gpd.read_file(f) for f in files]
    return pd.concat(sub_dfs)
