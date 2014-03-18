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

def rasterize_band(bnd, poly, f_img, f_shp):
	'''rasterize ploygon to match a raster band'''
	from osgeo import ogr, gdal
	import os

	_drv = ogr.GetDriverByName('ESRI Shapefile')

	if os.path.exists(f_shp):
		_drv.DeleteDataSource(f_shp)

	_shp = _drv.CreateDataSource(f_shp)
	_lyr = _shp.CreateLayer(f_shp[:-4], bnd.proj, ogr.wkbPolygon)

	_fea = ogr.Feature(_lyr.GetLayerDefn())
	_fea.SetGeometry(poly.poly)
	_lyr.CreateFeature(_fea)
	_fea.Destroy()

	import geo_raster_c as ge
	_img = ge.geo_raster.create(f_img, [bnd.height, bnd.width], bnd.geo_transform, bnd.proj.ExportToWkt())

	gdal.RasterizeLayer(_img.raster, [1], _lyr, burn_values=[1])
	return _img

def detect_corner_x(bnd, xd):
	import geo_base_c as gb
	assert(bnd.nodata != None)

	_geo = bnd.geo_transform
	_cel_x = _geo[1]
	_cel_y = _geo[5]

	_x = (_geo[0] - _cel_x / 2) if xd else (_geo[0]+_cel_x*bnd.width) \
			+ _cel_x / 2
	for _col in (xrange(bnd.width) if xd else xrange(bnd.width-1, 0, -1)):
		_x += _cel_x if xd else -1 * _cel_x
		_y = _geo[3] - _cel_y / 2
		for _row in xrange(bnd.height):
			_y += _cel_y

			_v = bnd.read_cell(_col, _row)
			if _v != bnd.nodata:
				return gb.geo_point(_x, _y, bnd.proj)

	return None

def detect_corner_y(bnd, yd):
	import geo_base_c as gb

	_geo = bnd.geo_transform
	_cel_x = _geo[1]
	_cel_y = _geo[5]

	_y = (_geo[3] - _cel_y / 2) if yd else ((_geo[3]+_cel_y*bnd.height)\
			+ _cel_y / 2)
	for _row in (xrange(bnd.height) if yd else xrange(bnd.height-1, 0, -1)):
		_y += _cel_y if yd else (-1 * _cel_y)
		_x = _geo[0] - _cel_x / 2
		for _col in xrange(bnd.width):
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

	import geo_base_c as gb
	_pol = gb.geo_polygon.from_pts(_pts, bnd.proj)

	return _pol

