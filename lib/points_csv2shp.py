#!/usr/bin/env python
# encoding: utf-8

'''
Create shapefile from a CSV file using coordinates from two columns of the file

Min Feng, Mar 26, 2012
'''
'''
Version: 0.5
Date: 2013-06-24 09:53:23
Note: updated to trim columns longer than 8 characters
'''

def create_ogr_field(col, typ):
	from osgeo import ogr

	if typ[0] == 'string':
		_fld = ogr.FieldDefn(col, ogr.OFTString)
		_fld.SetWidth(typ[1])
	elif typ[0] == 'float':
		_fld = ogr.FieldDefn(col, ogr.OFTReal)
	elif typ[0] == 'int':
		_fld = ogr.FieldDefn(col, ogr.OFTInteger)
	else:
		raise Exception('unsupported field type ' + typ[0])

	return _fld

def proj_from_epsg(code=4326):
	from osgeo import osr

	_proj = osr.SpatialReference()
	_proj.ImportFromEPSG(code)

	return _proj

def format_cols(cols):
	_cols = []
	for _c in cols:
		if len(_c) > 8:
			_c = _c[:8]
			if _c in _cols:
				for i in xrange(10):
					_c = _c[:6] + '_' + str(i)
					if _c not in _cols:
						break
		_cols.append(_c)
	return _cols

def csv2shapefile(f_csv, f_out, proj=0, fld_x=None, fld_y=None):
	import csv_util

	_cols, _typs, _vals = csv_util.read(f_csv)
	_cols = format_cols(_cols)

	if fld_x != None:
		_fld_x = fld_x
	else:
		_fld_x = 'lon' if 'lon' in _cols else 'x'

	if fld_y != None:
		_fld_y = fld_y
	else:
		_fld_y = 'lat' if 'lat' in _cols else 'y'

	print 'columns'
	for i in xrange(len(_cols)):
		print '+', _cols[i], ':', _typs[i]

	_proj = proj
	if _proj == 0 and _fld_x == 'lon' and _fld_y == 'lat':
		_proj = 4326

	print 'geo columns:', _fld_x, ',', _fld_y

	print 'proj:', _proj if _proj > 0 else 'none'

	from osgeo import ogr
	import os

	print 'write to\n>', f_out
	_fd_out = os.path.dirname(f_out)
	if _fd_out:
		os.path.exists(_fd_out) or os.makedirs(_fd_out)

	_drv = ogr.GetDriverByName("ESRI Shapefile")
	os.path.exists(f_out) and _drv.DeleteDataSource(f_out)

	_shp = _drv.CreateDataSource(f_out)
	_lyr = _shp.CreateLayer(os.path.basename(f_out)[:-4], proj_from_epsg(_proj) if _proj > 0 else None, ogr.wkbPoint)

	for i in xrange(len(_cols)):
		_lyr.CreateField(create_ogr_field(_cols[i].upper(), _typs[i]))

	for _vs in _vals:
		_feat = ogr.Feature(_lyr.GetLayerDefn())
		for i in xrange(len(_cols)):
			_feat.SetField(_cols[i].upper(), csv_util.parse_val(_typs[i], _vs[i]))

		_x = float(_vs[_cols.index(_fld_x)])
		_y = float(_vs[_cols.index(_fld_y)])

		_pt = ogr.Geometry(ogr.wkbPoint)
		_pt.SetPoint_2D(0, _x, _y)
		_feat.SetGeometry(_pt)

		_lyr.CreateFeature(_feat)
		_feat.Destroy()

def usage():
	import argparse, os

	_p = argparse.ArgumentParser()

	_p.add_argument('-i', '--input-csv', dest='input', required=True)
	_p.add_argument('--projection', dest='projection', type=int, default=0)
	_p.add_argument('--xy-columns', dest='columns', nargs=2, default=[None, None])
	_p.add_argument('-o', '--output-shp', dest='output')

	_opts = _p.parse_args()
	if not _opts.output:
		_opts.output = os.path.join(os.path.join(os.path.dirname(_opts.input), 'shp'), os.path.basename(_opts.input)[:-4] + '.shp')

	return _opts

if __name__ == '__main__':
	_opts = usage()
	csv2shapefile(_opts.input, _opts.output, _opts.projection, _opts.columns[0], _opts.columns[1])
