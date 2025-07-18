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

def rasterize(bnd, polys, f_img=None, f_shp=None, touched=True, pixel_type=None):
    '''rasterize ploygon to match a raster band'''
    from osgeo import ogr, gdal
    from . import geo_raster as ge
    from . import file_unzip
    import os
    
    with file_unzip.zip() as _zip:
        _f_shp = f_shp or _zip.generate_file('', '.shp')
        _f_img = f_img or _zip.generate_file('', '.img')
        
        _drv = ogr.GetDriverByName('ESRI Shapefile')
    
        if os.path.exists(_f_shp):
            _drv.DeleteDataSource(_f_shp)
    
        _shp = _drv.CreateDataSource(_f_shp)
        _lyr = _shp.CreateLayer(_f_shp[:-4], bnd.proj, ogr.wkbPolygon)
        
        _pps = [_p.project_to(bnd.proj) for _p in _to_list(polys, False)]
        for _poly in _pps:
            _fea = ogr.Feature(_lyr.GetLayerDefn())
            _fea.SetGeometry(_poly.poly)
            _lyr.CreateFeature(_fea)
            _fea.Destroy()
            
        _pixel_type = ge.pixel_type() if pixel_type is None else pixe_type
        _img = ge.geo_raster.create(_f_img, [bnd.height, bnd.width], bnd.geo_transform, \
                    bnd.proj.ExportToWkt(), pixel_type=_pixel_type)
        if _img is None:
            return None
            
        _opts = []
        if touched:
            _opts.append('ALL_TOUCHED=TRUE')
            
        # if attribute_name:
        #     _opts.append('ATTRIBUTE=value')
            
        gdal.RasterizeLayer(_img.raster, [1], _lyr, burn_values=[1], options=_opts)
        del _lyr, _shp, _drv

    return _img

rasterize_polygons = rasterize
rasterize_polygon = rasterize
rasterize_band = rasterize
    
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

def to_mask(bnd, poly, touched=True, f_img=None, f_shp=None):
    _bnd = rasterize(bnd, poly, f_img, f_shp, touched)
    if _bnd is None:
        return None
    
    return _bnd.get_band().cache()

def _to_list(poly, reproject=True):
    if isinstance(poly, list) or isinstance(poly, tuple):
        _ps = []
        _pj = None

        for _p in poly:
            if reproject:
                if _pj is None:
                    _pj = _p.proj
                else:
                    _p = _p.project_to(_pj)

            _ps.append(_p)
        
        return _ps
    else:
        return [poly]

def to_raster(poly, cell, ceil=True):
    _ps = _to_list(poly)

    _ext = None
    for _p in _ps:
        if _ext is None:
            _ext = _p.extent()
        else:
            _ext = _ext.union(_p.extent())

    _geo = [_ext.minx, cell, 0, _ext.maxy, 0, -cell]

    _col = _ext.width() / cell
    _row = _ext.height() / cell

    import math
    _col = int(math.ceil(_col)) if ceil else int(_col)
    _row = int(math.ceil(_row)) if ceil else int(_row)

    from gio import geo_raster as ge
    return ge.geo_band_info(_geo, _col, _row, _ps[0].proj)
   
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
    