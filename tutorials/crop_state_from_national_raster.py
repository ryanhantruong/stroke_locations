# import fiona
import rasterio
import rasterio.mask as rmask
import shapely.geometry as shgeo
import timeit
import geopandas as gpd
from fiona.crs import from_epsg
# import matplotlib.pyplot as plt
import json
import pycrs

#state bound
state_fip = '25'
gdf = gpd.read_file('census_data/tl_2018_us_state/tl_2018_us_state.shp')
minx,miny,maxx,maxy = gdf.loc[gdf.STATEFP==state_fip,'geometry'].iloc[0].bounds
# minx, miny = -71.181316, 42.302193
# maxx, maxy = -71.031258, 42.371605
bbox = shgeo.box(minx, miny, maxx, maxy)
geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=from_epsg(4326))

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

with rasterio.Env():
    with rasterio.open(
            'census_data/land_coverage/NLCD_2016_Land_Cover_L48_20190424.img',
            'r') as src:
        # Convert to src coordinate system
        geo = geo.to_crs(crs=src.crs)
        coords = getFeatures(geo)
        # Crop
        print("About to crop")
        st = timeit.timeit()
        out_img, out_transform = rmask.mask(dataset=src, shapes=coords, crop=True)
        en = timeit.timeit()
        print(f'Finished cropping {en-st}')
        # Contruct metadata to save
        kwargs = src.meta.copy()
        kwargs.update({
            'driver':'GTiff',
            'transform': out_transform,
            'height': out_img.shape[1],
            'width': out_img.shape[2]
        })
        with rasterio.open(f'census_data/land_coverage/state{state_fip}.tif', 'w',
                           **kwargs) as dst:
            print('Writing to file')
            dst.write(out_img)


# # review output
# with rasterio.open(f'census_data/land_coverage/state{state_fip}.tif') as clipped:
#     array = clipped.read(1)
#     plt.imshow(array)
#     plt.show()
# # from rasterio.plot import show
# # %matplotlib inline
