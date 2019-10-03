from pathlib import Path
import pandas as pd
import us
import download
import geopandas as gpd
import zipfile

# STEP 0
# Download data manually from American Fact Finder
#   Go to Advanced Search
#   Geography: Block 100, Topic: Total Population, Table : P12 - SEX BY AGE
#   Save each batch into format: census_data/SF2010_zips/SF2010_{state_abbr}_{batch_num}

CENSUS_DATA_PATH = Path('census_data')
if not CENSUS_DATA_PATH.exists(): CENSUS_DATA_PATH.mkdir()


def get_us_county_shapefiles():
    filepath = CENSUS_DATA_PATH / 'tl_2018_us_county' / 'tl_2018_us_county.shp'
    if not filepath.exists():
        # download from internet
        shape_link = 'https://www2.census.gov/geo/tiger/TIGER2018/COUNTY/'\
        +'tl_2018_us_county.zip'
        zipped = download.download_file(shape_link, "US Counties")
        with zipfile.ZipFile(zipped) as z:
            z.extractall(filepath.parent)
    gdf = gpd.read_file('census_data/tl_2018_us_county/tl_2018_us_county.shp')
    return gdf


def are_all_counties_are_included(sfs, gdf):
    sfs['COUNTYFP'] = sfs['GEO.id2'].apply(lambda x: x[:5])
    state_counties = gdf.loc[gdf.STATEFP == state_fip, 'GEOID']
    result = True
    if not state_counties.isin(sfs.COUNTYFP).all():
        print(
            f'{state_abbr} dont have population count for all of its counties!'
        )
        notin = state_counties[~state_counties.isin(sfs.COUNTYFP)]
        notinstr = ', '.join(notin)
        print(f'Counties missing in {state_abbr}: {notinstr}')
        result = False
    sfs.drop('COUNTYFP', axis=1, inplace=True)
    return result


# STEP 1
# Run this loop
SHAPEFILE_OUTPATH = str(CENSUS_DATA_PATH / 'census_blocks_shapefiles')
# Shape file county level
gdf = get_us_county_shapefiles()
# Summary files manually selected and downloaded from American Fact Finder
SF2010_DOWNLOADED_PATH = CENSUS_DATA_PATH / 'SF2010_zips'
SF2010_DOWNLOADED_FILENAME = 'DEC_10_SF1_P12_with_ann.csv'
SF2010_OUTPATH = CENSUS_DATA_PATH / 'SF2010'
# One iteration for each state
state_abbrs = ['NH', 'NJ', 'CT', 'RI', 'ME', 'VT']
for state_abbr in state_abbrs:

    state_fip = us.states.lookup(state_abbr).fips

    # Download shapefile for this state, block level:
    shape_link = 'https://www2.census.gov/geo/tiger/TIGER2018/TABBLOCK/'\
    + f'tl_2018_{state_fip}_tabblock10.zip'
    print(shape_link)
    zipped = download.download_file(shape_link, state_abbr)
    with zipfile.ZipFile(zipped) as z:
        z.extractall(SHAPEFILE_OUTPATH)

    # 2 diff name format depends on which state so just get both
    sfpaths = [SF2010_DOWNLOADED_PATH.glob(f'{state_abbr}_download_?')]
    sfpaths += [SF2010_DOWNLOADED_PATH.glob(f'SF2010_{state_abbr}_?')]

    dflist = []
    for i, sfp in enumerate(sfpaths):
        if i > 0:
            dflist.append(
                pd.read_csv(sfp / SF2010_DOWNLOADED_FILENAME,
                            dtype=str,
                            skiprows=[1]))
        else:
            dflist.append(
                pd.read_csv(sfp / SF2010_DOWNLOADED_FILENAME, dtype=str))
    sfs = pd.concat(dflist, ignore_index=True).drop_duplicates(
    )  # incase a county is included twice

    # check to make sure all counties are included in analysis
    checkresult = are_all_counties_are_included(sfs, gdf)
    if checkresult:
        sfs.to_csv(SF2010_OUTPATH /
                   f'{state_abbr}_blocks_from_all_counties.csv',
                   index=False)
