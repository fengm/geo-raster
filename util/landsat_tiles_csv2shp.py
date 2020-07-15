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
	import gio.csv_util
	import os

	_tiles, _landsat_schema, _landsat_proj, _landsat_geom = load_landsat_tile(f_landsat)
	_cols, _typs, _vals = gio.csv_util.read(f_csv)

	print('columns')
	for i in range(len(_cols)):
		print('+', _cols[i], ':', _typs[i])

	_fd_out = os.path.dirname(f_out)
	if _fd_out:
		os.path.exists(_fd_out) or os.makedirs(_fd_out)

	_drv = ogr.GetDriverByName("ESRI Shapefile")
	os.path.exists(f_out) and _drv.DeleteDataSource(f_out)

	_shp = _drv.CreateDataSource(f_out)
	_lyr = _shp.CreateLayer(os.path.basename(f_out)[:-4], _landsat_proj, _landsat_geom)

	for i in range(len(_landsat_schema)):
		_lyr.CreateField(_landsat_schema[i])

	for i in range(len(_cols)):
		_lyr.CreateField(create_ogr_field(_cols[i].upper(), _typs[i]))

	for _vs in _vals:
		_feat = ogr.Feature(_lyr.GetLayerDefn())
		for i in range(len(_cols)):
			_feat.SetField(_cols[i].upper(), gio.csv_util.parse_val(_typs[i], _vs[i]))

		_tile = _vs[_cols.index(col)]
		if _tile not in _tiles:
			logging.warning('tile %s not found' % _tile)
			continue
		_temp = _tiles[_tile]
		for i in range(len(_landsat_schema)):
			_field = _landsat_schema[i]
			_feat.SetField(_field.name, _temp.items()[_landsat_schema[i].name])
		_feat.SetGeometry(_temp.geometry())

		_lyr.CreateFeature(_feat)
		_feat.Destroy()

def main(opts):
	import os
	if not opts.output:
		opts.output = os.path.join(os.path.dirname(opts.input), \
				os.path.basename(opts.input)[:-4] + '.shp')

	_f_ref = opts.tile_file
	if not _f_ref:
		if opts.tile_tag == 'wrs2':
			_f_ref = os.environ['D_DATA_WRS2']
		elif opts.tile_tag == 'wrs1':
			_f_ref = os.environ['D_DATA_WRS1']
		else:
			raise Exception('unsupported tiling system tag (%s)' % opts.tile_tag)
			
	from gio import file_mag
	from gio import file_unzip
	import os
	
	with file_unzip.file_unzip() as _zip:
		_d_out = _zip.generate_file()
		os.makedirs(_d_out)
		
		f_out = opts.output
		
		_f_out = os.path.join(_d_out, os.path.basename(f_out))
		csv2shapefile(file_mag.get(opts.input).get(), _f_out, opts.column, _f_ref)
		
		_d_ttt = os.path.dirname(f_out)
		if not _d_ttt:
			_d_ttt = os.path.dirname(os.path.abspath(f_out))
			
		print('write to\n>', f_out)
		file_unzip.compress_folder(_d_out, _d_ttt, [])

def usage():
	_p = environ_mag.usage()

	_p.add_argument('-i', '--input-csv', dest='input', required=True)
	_p.add_argument('--tile-column', dest='column', default='tile')
	_p.add_argument('--tile-file', dest='tile_file')
	_p.add_argument('--tiling', dest='tile_tag', default='wrs2')
	_p.add_argument('-o', '--output-shp', dest='output', required=False)

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

