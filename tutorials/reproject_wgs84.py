import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
''' Source: https://rasterio.readthedocs.io/en/stable/topics/reproject.html '''

dst_crs = 'EPSG:4326'  # normal long lat WGS84
state_fip = '25'
with rasterio.open(f'census_data/land_coverage/state{state_fip}.tif') as src:
    transform, width, height = calculate_default_transform(
        src_crs=src.crs, dst_crs=dst_crs, width=src.width, height=src.height,
        left = src.bounds.left, bottom = src.bounds.bottom,right = src.bounds.right,
        top = src.bounds.top)
    kwargs = src.meta.copy()
    kwargs.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })

    with rasterio.open(f'census_data/land_coverage/state{state_fip}_WGS84.tif',
                       'w', **kwargs) as dst:
        for i in range(1, src.count + 1):
            reproject(source=rasterio.band(src, i),
                      destination=rasterio.band(dst, i),
                      # src_transform=src.transform,
                      # src_crs=src.crs,
                      # dst_transform=transform,
                      # dst_crs=dst_crs,
                      resampling=Resampling.nearest)
