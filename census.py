'''Download and read population files from the 2010 census.'''
import os
import string
import zipfile
import warnings
import pandas as pd
import geopandas as gpd
import us
import download
from pathlib import Path

CENSUS_FOLDER = os.path.join('data', 'census')
CENSUS_SUMMARYFILE_PATH = Path('census_data/SF2010')
SHAPEFILE_PATH = Path('census_data/census_blocks_shapefiles')
if not CENSUS_SUMMARYFILE_PATH.exists():
    print(f'{CENSUS_SUMMARYFILE_PATH} not found' +
          ', need to generate summaryfiles to use read_states_age_adjusted()')

if not os.path.isdir(CENSUS_FOLDER):
    os.makedirs(CENSUS_FOLDER)


def read_states(states=['Connecticut']):
    '''
    Get census data for given states, downloading it if necessary.
        States can be passed by name, abbreviation, or FIPS code
        Returns data and a list of abbreviations for all states used
    '''
    states = _normalize_states(states)
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
    return pd.concat(sub_dfs), [st.abbr for st in states]


def read_states_age_adjusted(states=['New York']):
    print(f"States entered: {', '.join(states)}")
    states = _normalize_states(states)
    state_abbrs = [st.abbr for st in states]
    print(f"States to read: {', '.join(state_abbrs)}")
    dflist = []
    gdflist = []
    for state in states:
        spath = CENSUS_SUMMARYFILE_PATH / f'{state.abbr}_blocks_from_all_counties.csv'
        if not spath.exists():
            print(f"{spath} dont exist so skip {state.abbr}")
            continue
        print(f"Reading {spath}")
        dflist.append(
            pd.read_csv(spath, dtype=str,
                        skiprows=[1]).assign(STATEABBR=state.abbr))
        gpath = SHAPEFILE_PATH / f'tl_2018_{state.fips}_tabblock10.shp'
        print(f"Reading {gpath}")
        gdflist.append(gpd.read_file(gpath))
    dfs = pd.concat(dflist, ignore_index=True)
    gdfs = gpd.GeoDataFrame(pd.concat(gdflist, ignore_index=True))
    # Age group columns of 65 years or older for male and female
    male_count_columns = [f'D{str(x).zfill(3)}' for x in range(20, 25 + 1)]
    female_count_columns = [f'D{str(x).zfill(3)}' for x in range(44, 49 + 1)]
    dfs['over_65'] = dfs[male_count_columns +
                         female_count_columns].astype(int).sum(axis=1)
    print("Combining shapefiles and population counts")
    outdfs=gdfs.merge(dfs, right_on='GEO.id2', left_on='GEOID10')
    return outdfs, state_abbrs


def _normalize_states(states):
    '''
    Convert states to standardized names
    '''
    standard = []
    for state in states:
        found_state = us.states.lookup(state.strip(string.punctuation))
        if found_state is None:
            raise ValueError(f"Couldn't match '{state}' to a state")
        standard.append(found_state)
    return standard


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
