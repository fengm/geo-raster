#!/usr/bin/env python
# encoding: utf-8

'''
File: raster_extent2shp.py
Author: Min Feng
Version: 1.0
Create: 2012-03-28 15:07:02
Description: Retrieve coverages from a list of rasters and save
the coverages into a shapefile
'''
'''
Version: 1.1
Date: 2012-09-29 15:06:45
Note: Updated to support gzipped files
'''

def create_polygon(ext):
	from osgeo import ogr

	_ring = ogr.Geometry(type=ogr.wkbLinearRing)
	_ring.AddPoint_2D(ext.minx, ext.miny)
	_ring.AddPoint_2D(ext.minx, ext.maxy)
	_ring.AddPoint_2D(ext.maxx, ext.maxy)
	_ring.AddPoint_2D(ext.maxx, ext.miny)
	_ring.AddPoint_2D(ext.minx, ext.miny)

	_poly = ogr.Geometry(type=ogr.wkbPolygon)
	_poly.AddGeometry(_ring)

	return _poly

def open_file(f, fzip):
	import gio.geo_raster as ge

	_cs = f.split('#')

	_f = _cs[0]
	if _f.endswith('gz'):
		_f = fzip.unzip(_f)

	_img = ge.geo_raster.open(_f)
	if _f.lower().endswith('.hdf'):
		if len(_cs) >= 2:
			return _img.get_subdataset(_cs[1])
		return _img.get_subdataset(_img.sub_datasets()[0][0])

	return _img

def _geo_line(ext, proj):
	from osgeo import ogr

	_line = ogr.Geometry(ogr.wkbLineString)

	# _leng = ext.height()
	# if _leng <= 0.0:

	_line.AddPoint(180.0, min(ext.maxy + 5.0, 89.5))
	_line.AddPoint(180.0, max(ext.miny - 5.0, -89.5))

	_line.AssignSpatialReference(proj)
	return _line

def _project_to(poly, proj):
	from osgeo import ogr
	_poly = ogr.CreateGeometryFromWkt(poly.ExportToWkt())
	_poly.AssignSpatialReference(poly.GetSpatialReference())

	_poly.TransformTo(proj)
	return _poly

def _split_box(ext):
	import gio.geo_base as gb

	_pt = lambda x, y: gb.geo_point(x, y)
	_pol1 = gb.geo_polygon.from_pts([_pt(-120, ext.miny), _pt(-120, ext.maxy), _pt(-179.999, ext.maxy), \
			_pt(-179.999, ext.miny)], ext.proj).segment_ratio(10)
	_pol2 = gb.geo_polygon.from_pts([_pt(120, ext.miny), _pt(120, ext.maxy), _pt(179.999, ext.maxy), \
			_pt(179.999, ext.miny)], ext.proj).segment_ratio(10)

	return _pol1, _pol2

def _split_polygons(ext, prj):
	# import geo_base_c as gb

	_prj1 = ext.proj
	_prj2 = prj

	_ext = ext.project_to(_prj2)
	_box = _ext.extent()

	_lin2 = _geo_line(_box, _prj2)
	_lin1 = _project_to(_lin2, _prj1)

	# gb.output_polygons([ext], 'test5.shp')
	# from osgeo import ogr
	# gb.output_geometries([_lin1], _prj1, ogr.wkbLineString, 'test6.shp')
	# gb.output_geometries([_lin2], _prj2, ogr.wkbLineString, 'test7.shp')
	# gb.output_polygons([_ext], 'test8.shp')

	if ext.poly.Intersect(_lin1):
		_pol1, _pol2 = _split_box(_box)

		_ara1 = ext.intersect(_pol1.project_to(_prj1))
		_ara2 = ext.intersect(_pol2.project_to(_prj1))

		# gb.output_polygons([ext, _pol1.project_to(_prj1)], 'test1.shp')
		# gb.output_polygons([_pol1], 'test2.shp')
		# gb.output_polygons([_pol1.project_to(_prj1)], 'test3.shp')
		# gb.output_polygons([_box.to_polygon()], 'test4.shp')
		# gb.output_polygons([_ara1], 'test5.shp')
		# gb.output_polygons([_ara2], 'test6.shp')
		# gb.output_polygons([_ara1.project_to(_prj2), _ara2.project_to(_prj2)], 'test7.shp')

		# import sys
		# sys.exit(0)

		return [_ara1.project_to(_prj2), _ara2.project_to(_prj2)]

	return [_ext]

def _generate_extent(f, proj):
	import gio.file_unzip
	import re

	_f = f
	_re = re.match('/a/[^/]+(/.+)', _f)

	if _re:
		_f = _re.group(1)

	with gio.file_unzip.file_unzip() as _zip:
		_img = open_file(_f, _zip)
		_bnd = _img.get_band()

		from gio import geo_base as gb
		_ext = gb.geo_polygon.from_raster(_bnd.raster)
		_geos = [_ext]

		if proj != None:
			if proj == 4326:
				from gio import geo_raster as ge
				_geos = _split_polygons(_ext, ge.proj_from_epsg(proj))
			else:
				_ext = _ext.project_to(proj)
				_geos = [_ext]

		_pols = []
		for _geo in _geos:
			if _geo == None or _geo.poly == None:
				continue
			_pols.append(_geo.poly.ExportToWkb())

		return [_f, _pols]

def _generate_extents(fs, proj, opts):
	from gio import multi_task

	_res = {}
	for _f, _p in multi_task.run(_generate_extent, [(_f, proj) for _f in fs], opts):
		_res[_f] = _p

	return _res

def generate_shp(fs, proj, f_out, fzip, opts):
	from gio import geo_raster as ge
	from osgeo import ogr
	from gio.progress_percentage import progress_percentage
	import os

	_pols = _generate_extents(fs, proj, opts)

	# use projection of the first file if no target projection specified
	_proj = open_file(fs[0], fzip).projection_obj
	print _proj

	_proj = (_proj) if proj == None else ge.proj_from_epsg(proj)
	fzip.clean()

	_drv = ogr.GetDriverByName('ESRI Shapefile')
	os.path.exists(f_out) and _drv.DeleteDataSource(f_out)
	_shp = _drv.CreateDataSource(f_out)
	_lyr = _shp.CreateLayer(filter(lambda x: x[:-4] if x.lower().endswith('.shp') else x, \
			os.path.basename(f_out)[:-4]), _proj, ogr.wkbPolygon)

	_fld = ogr.FieldDefn('FILE', ogr.OFTString)
	_fld.SetWidth(254)
	_lyr.CreateField(_fld)

	_perc = progress_percentage(len(_pols.keys()))
	for _f, _ps in _pols.items():
		_perc.next()

		for _p in _ps:
			if _p == None:
				continue

			_ftr = ogr.Feature(_lyr.GetLayerDefn())
			_ftr.SetField('file', _f)
			_ftr.SetGeometry(ogr.CreateGeometryFromWkb(_p))
			_lyr.CreateFeature(_ftr)
			_ftr.Destroy()

		fzip.clean()

	_perc.done()

def generate_shp_from_file(fs, dataset, proj, f_out, absp, d_tmp):
	import os

	_fs = []
	for i in xrange(len(fs)):
		_p = os.path.abspath(fs[i])
		if absp:
			_p = os.path.abspath(_p)

		if dataset:
			_p = _p + '#' + dataset

		_fs.append(_p)

	from gio import file_unzip
	with file_unzip.file_unzip(d_tmp) as _zip:
		generate_shp(_fs, proj, f_out, _zip)

def generate_shp_from_list(f_list, dataset, proj, f_out, absp, d_tmp, opts):
	_fs = [(_l.strip() + '#' + dataset if dataset else _l.strip()) \
			for _l in open(f_list).read().splitlines() if _l.strip()]
	if len(_fs) == 0:
		print 'found no files'
		return

	print 'found', len(_fs), 'files in list', f_list
	print '--------------'
	for _f in _fs[: min(len(_fs), 2)]:
		print ' >', _f
	print '  ...'

	import gio.file_unzip
	_zip = gio.file_unzip.file_unzip(d_tmp)
	try:
		generate_shp(_fs, proj, f_out, _zip, opts)
	finally:
		_zip.clean()

def generate_shp_from_folder(fd, dataset, proj, f_out, absp, d_tmp, opts):
	import os

	_fs = []
	for _root, _dirs, _files in os.walk(fd):
		for _f in _files:
			if _f.lower()[-4:] in ['.tif', '.img', '.hdf'] or \
					_f.lower()[-7:] in ['.tif.gz', '.img.gz', '.hdf.gz']:
				_p = os.path.join(_root, _f)

				if absp:
					_p = os.path.abspath(_p)

				if dataset:
					_p = _p + '#' + dataset
				_fs.append(_p)
	if len(_fs) == 0:
		print 'found no files'
		return

	print 'found', len(_fs), 'files in', fd
	print '--------------'
	for _f in _fs[: min(len(_fs), 2)]:
		print ' >', _f
	print '  ...'

	import gio.file_unzip
	_zip = gio.file_unzip.file_unzip(d_tmp)
	try:
		generate_shp(_fs, proj, f_out, _zip, opts)
	finally:
		_zip.clean()

def main():
	_opts = _init_env()

	import os

	if os.path.isdir(_opts.input):
		return generate_shp_from_folder(_opts.input, _opts.dataset,
				_opts.projection, _opts.output, _opts.absolutepath,
				_opts.temp_path, _opts)

	_f_inp = _opts.input.lower()
	if _f_inp.endswith('.txt'):
		return generate_shp_from_list(_opts.input, _opts.dataset, _opts.projection,
				_opts.output, _opts.absolutepath, _opts.temp_path, _opts)

	print 'unknown inputs'

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

	_p.add_argument('-i', '--input', dest='input')
	_p.add_argument('-p', '--projection', dest='projection', type=int)
	_p.add_argument('-n', '--dataset', dest='dataset')
	_p.add_argument('-o', '--ouput-file', dest='output', required=True)
	_p.add_argument('-t', '--temp-path', dest='temp_path')
	_p.add_argument('-a', '--absolute-path', dest='absolutepath',
			action='store_true')

	import gio.multi_task
	gio.multi_task.add_task_opts(_p)

	return _p.parse_args()

def _init_env():
	import os, sys

	_dirs = ['lib', 'libs']
	_d_ins = [os.path.join(sys.path[0], _d) for _d in _dirs if \
			os.path.exists(os.path.join(sys.path[0], _d))]
	sys.path = [sys.path[0]] + _d_ins + sys.path[1:]

	_opts = _usage()

	from gio import logging_util
	logging_util.init(_opts.logging)

	from gio import config
	config.load(_opts.config)

	from gio import file_unzip as fz
	fz.clean(fz.default_dir(_opts.temp))

	return _opts

if __name__ == '__main__':
	main()

