#!/usr/bin/env python
# encoding: utf-8

'''
Create shapefile from a CSV file with joining a column to the Landsat
	WRS tiling file

Min Feng, Mar 26, 2012
'''

import logging

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

def load_landsat_tile(f_shp, tile_col='PATHROW'):
	from osgeo import ogr
	import os

	_drv = ogr.GetDriverByName("ESRI Shapefile")
	_shp = _drv.Open(f_shp)
	_lyr = _shp.GetLayer(os.path.basename(f_shp)[:-4])

	_vs = {}
	for _fet in _lyr:
		_tile = _fet.items()[tile_col]
		_vs[_tile] = _fet

	return _vs, _lyr.schema, _lyr.GetSpatialRef(), _lyr.GetLayerDefn().GetGeomType()

def csv2shapefile(f_csv, f_out, col, f_landsat):
	from osgeo import ogr
	import csv_util, sys
	import os

	_tiles, _landsat_schema, _landsat_proj, _landsat_geom = load_landsat_tile(os.path.join(sys.path[0], f_landsat))
	_cols, _typs, _vals = csv_util.read(f_csv)

	print 'columns'
	for i in xrange(len(_cols)):
		print '+', _cols[i], ':', _typs[i]

	print 'write to\n>', f_out
	_fd_out = os.path.dirname(f_out)
	if _fd_out:
		os.path.exists(_fd_out) or os.makedirs(_fd_out)

	_drv = ogr.GetDriverByName("ESRI Shapefile")
	os.path.exists(f_out) and _drv.DeleteDataSource(f_out)

	_shp = _drv.CreateDataSource(f_out)
	_lyr = _shp.CreateLayer(os.path.basename(f_out)[:-4], _landsat_proj, _landsat_geom)

	for i in xrange(len(_landsat_schema)):
		_lyr.CreateField(_landsat_schema[i])

	for i in xrange(len(_cols)):
		_lyr.CreateField(create_ogr_field(_cols[i].upper(), _typs[i]))

	for _vs in _vals:
		_feat = ogr.Feature(_lyr.GetLayerDefn())
		for i in xrange(len(_cols)):
			_feat.SetField(_cols[i].upper(), csv_util.parse_val(_typs[i], _vs[i]))

		_tile = _vs[_cols.index(col)]
		if _tile not in _tiles:
			logging.warning('tile %s not found' % _tile)
			continue
		_temp = _tiles[_tile]
		for i in xrange(len(_landsat_schema)):
			_field = _landsat_schema[i]
			_feat.SetField(_field.name, _temp.items()[_landsat_schema[i].name])
		_feat.SetGeometry(_temp.geometry())

		_lyr.CreateFeature(_feat)
		_feat.Destroy()

def usage():
	import argparse, os

	_p = argparse.ArgumentParser()

	_p.add_argument('-i', '--input-csv', dest='input', required=True)
	_p.add_argument('--tile-column', dest='column', default='tile')
	_p.add_argument('--tile-file', dest='tile_file')
	_p.add_argument('--tiling', dest='tile_tag', default='wrs2')
	_p.add_argument('-o', '--output-shp', dest='output', required=False)

	_opts = _p.parse_args()
	if not _opts.output:
		_opts.output = os.path.join(os.path.join(os.path.dirname(_opts.input), 'shp'), os.path.basename(_opts.input)[:-4] + '.shp')

	return _opts

if __name__ == '__main__':
	_opts = usage()

	_f_ref = _opts.tile_file
	if not _f_ref:
		import os, sys

		if _opts.tile_tag == 'wrs2':
			_f_ref = os.path.join(sys.path[0], 'data/landsat/wrs2_descending.shp')
		elif _opts.tile_tag == 'wrs1':
			_f_ref = os.path.join(sys.path[0], 'data/landsat/wrs1_descending.shp')
		else:
			raise Exception('unsupported tiling system tag (%s)' % _opts.tile_tag)

	csv2shapefile(_opts.input, _opts.output, _opts.column, _f_ref)

