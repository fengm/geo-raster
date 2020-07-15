'''
File: rasterize_band.py
Author: Min Feng
Version: 0.1
Create: 2013-02-07 22:29:14
Description: Rasterize a polygon to a raster
'''
'''
Version: 0.2
Date: 2013-11-15 09:48:11
Note: Added the function for detecting the polygon extent for a Landsat scene
'''

def rasterize_polygons(bnd, polys, f_img, f_shp, touched=True):
    '''rasterize ploygon to match a raster band'''
    from osgeo import ogr, gdal
    import os

    _drv = ogr.GetDriverByName('ESRI Shapefile')

    if os.path.exists(f_shp):
        _drv.DeleteDataSource(f_shp)

    _shp = _drv.CreateDataSource(f_shp)
    _lyr = _shp.CreateLayer(f_shp[:-4], bnd.proj, ogr.wkbPolygon)

    for _poly in polys:
        _fea = ogr.Feature(_lyr.GetLayerDefn())
        _fea.SetGeometry(_poly.poly)
        _lyr.CreateFeature(_fea)
        _fea.Destroy()
        
    from . import geo_raster as ge
    _img = ge.geo_raster.create(f_img, [bnd.height, bnd.width], bnd.geo_transform, bnd.proj.ExportToWkt())
    
    gdal.RasterizeLayer(_img.raster, [1], _lyr, burn_values=[1], options=['ALL_TOUCHED=TRUE'] if touched else [])
    del _lyr, _shp, _drv

    return _img

def rasterize_polygon(bnd, poly, f_img, f_shp, touched=True):
    '''rasterize ploygon to match a raster band'''
    from osgeo import ogr, gdal
    import os

    _drv = ogr.GetDriverByName('ESRI Shapefile')

    if os.path.exists(f_shp):
        _drv.DeleteDataSource(f_shp)

    _shp = _drv.CreateDataSource(f_shp)
    _lyr = _shp.CreateLayer(os.path.basename(f_shp)[:-4], bnd.proj, ogr.wkbPolygon)

    _fea = ogr.Feature(_lyr.GetLayerDefn())
    _fea.SetGeometry(poly.poly)
    _lyr.CreateFeature(_fea)
    _fea.Destroy()

    from . import geo_raster as ge
    _img = ge.geo_raster.create(f_img, [bnd.height, bnd.width], bnd.geo_transform, bnd.proj.ExportToWkt())

    gdal.RasterizeLayer(_img.raster, [1], _lyr, burn_values=[1], options=['ALL_TOUCHED=TRUE'] if touched else [])
    del _lyr, _shp, _drv
    
    return _img

def rasterize_band(bnd, poly, f_img, f_shp):
    return rasterize_polygon(bnd, poly, f_img, f_shp)

def detect_corner_x(bnd, xd):
    from . import geo_base as gb
    assert(bnd.nodata != None)

    _geo = bnd.geo_transform
    _cel_x = _geo[1]
    _cel_y = _geo[5]

    _x = (_geo[0] - _cel_x / 2) if xd else (_geo[0]+_cel_x*bnd.width) \
            + _cel_x / 2
    for _col in (range(bnd.width) if xd else range(bnd.width-1, 0, -1)):
        _x += _cel_x if xd else -1 * _cel_x
        _y = _geo[3] - _cel_y / 2
        for _row in range(bnd.height):
            _y += _cel_y

            _v = bnd.read_cell(_col, _row)
            if _v != bnd.nodata:
                return gb.geo_point(_x, _y, bnd.proj)

    return None

def detect_corner_y(bnd, yd):
    from . import geo_base as gb

    _geo = bnd.geo_transform
    _cel_x = _geo[1]
    _cel_y = _geo[5]

    _y = (_geo[3] - _cel_y / 2) if yd else ((_geo[3]+_cel_y*bnd.height)\
            + _cel_y / 2)
    for _row in (range(bnd.height) if yd else range(bnd.height-1, 0, -1)):
        _y += _cel_y if yd else (-1 * _cel_y)
        _x = _geo[0] - _cel_x / 2
        for _col in range(bnd.width):
            _x += _cel_x

            _v = bnd.read_cell(_col, _row)
            if _v != bnd.nodata:
                return gb.geo_point(_x, _y, bnd.proj)

    return None

def detect_landsat_extent(bnd):
    '''detect the rectangle extent for a Landsat band. It also works for other images with extent'''
    _pts = []
    _pts.append(detect_corner_x(bnd, True))
    _pts.append(detect_corner_y(bnd, True))
    _pts.append(detect_corner_x(bnd, False))
    _pts.append(detect_corner_y(bnd, False))

    if None in _pts:
        return None

    import geo_base as gb
    _pol = gb.geo_polygon.from_pts(_pts, bnd.proj)

    return _pol

def to_mask(bnd, poly, f_img=None, f_shp=None, touched=True):
    from gio import file_unzip
    with file_unzip.zip() as _zip:
        _f_img = f_img if f_img else _zip.generate_file('', '.img')
        _f_shp = f_shp if f_shp else _zip.generate_file('', '.shp')
        
        if isinstance(poly, list) or isinstance(poly, tuple):
            _ps = poly
        else:
            _ps = [poly]
        
        _ps = [_p.project_to(bnd.proj) for _p in _ps]
        return rasterize_polygons(bnd, _ps, _f_img, _f_shp, touched).get_band().cache()

def to_raster(poly, cell, ceil=True):
    import math
    
    _ext = poly.extent()
    _geo = [_ext.minx, cell, 0, _ext.maxy, 0, -cell]

    _col = _ext.width() / cell
    _row = _ext.height() / cell

    _col = int(math.ceil(_col)) if ceil else int(_col)
    _row = int(math.ceil(_row)) if ceil else int(_row)

    from gio import geo_raster as ge
    return ge.geo_band_info(_geo, _col, _row, poly.proj)
   
def mask(bnd, poly, touched=True):
    if bnd.nodata is None:
        raise Exception('nodata needs to be set for the input raster')
        
    _b = to_mask(bnd, poly, touched=touched)
    bnd.data[_b.data != 1] = bnd.nodata
    return bnd

def extract(bnd, poly, cell, ceil=True, touched=True):
    if bnd.nodata is None:
        raise Exception('nodata needs to be set for the input raster')
        
    _b = to_mask(to_raster(poly, cell, ceil), poly, touched=touched)
    _o = bnd.read_block(_b)
    _o.data[_b.data != 1] = _o.nodata
    return _o
    