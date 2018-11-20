'''Download and read population files from the 2010 census.'''
import os
import zipfile
import warnings
import pandas as pd
import geopandas as gpd
import us
import download


CENSUS_FOLDER = os.path.join('data', 'census')
if not os.path.isdir(CENSUS_FOLDER):
    os.makedirs(CENSUS_FOLDER)


def read_states(states=['Connecticut']):
    '''
    Get census data for given states, downloading it if necessary.
        States can be passed by name, abbreviation, or FIPS code
    '''
    states = [us.states.lookup(st) for st in states]
    files = []
    for state in states:
        d = _get_path(state)
        if not os.path.isdir(d):
            _download_data(state)
        files_found = 0
        for f in os.listdir(d):
            if f.endswith('.shp'):
                files.append(os.path.join(d, f))
                files_found += 1
        if files_found == 0:
            mes = f'No data found for {state.name}.'
            mes += f'\n\tDelete `{_get_path(state)}`'
            mes += ' and run again to redownload'
            warnings.warn(mes)
    sub_dfs = [gpd.read_file(f) for f in files]
    return pd.concat(sub_dfs)


def _get_path(state):
    '''
    Get the path to the census directory for this state
    '''
    return os.path.join(CENSUS_FOLDER, state.name)


def _ftp_path(state):
    '''
    Get the path to the ftp file for this state
    '''
    name = f'tabblock2010_{state.fips}_pophu.zip'
    return 'ftp://ftp2.census.gov/geo/tiger/TIGER2010BLKPOPHU/' + name


def _download_data(state):
    '''
    Download census data for the given state and unzip the file into the
        expected directory.
    '''
    zipped = download.download_file(_ftp_path(state), state.name)

    with zipfile.ZipFile(zipped) as z:
        z.extractall(_get_path(state))
