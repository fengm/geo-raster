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
	import geo_raster

	_cs = f.split('#')

	_f = _cs[0]
	if _f.endswith('gz'):
		_f = fzip.unzip(_f)

	_img = geo_raster.geo_raster.open(_f)
	if _f.lower().endswith('.hdf'):
		if len(_cs) >= 2:
			return _img.get_subdataset(_cs[1])
		return _img.get_subdataset(_img.sub_datasets()[0][0])

	return _img

def generate_shp(fs, proj, f_out, fzip):
	import geo_raster, geo_raster_ex
	from osgeo import ogr
	from progress_percentage import progress_percentage
	import os

	# use projection of the first file if no target projection specified
	_proj = (open_file(fs[0], fzip).projection_obj) if proj == None else geo_raster.proj_from_epsg(proj)
	fzip.clean(False)

	_drv = ogr.GetDriverByName('ESRI Shapefile')
	os.path.exists(f_out) and _drv.DeleteDataSource(f_out)
	_shp = _drv.CreateDataSource(f_out)
	_lyr = _shp.CreateLayer(filter(lambda x: x[:-4] if x.lower().endswith('.shp') else x, os.path.basename(f_out)[:-4]), _proj, ogr.wkbPolygon)

	_fld = ogr.FieldDefn('file', ogr.OFTString)
	_fld.SetWidth(254)
	_lyr.CreateField(_fld)

	_perc = progress_percentage(len(fs))
	for _f in fs:
		_perc.next()

		_img = open_file(_f, fzip)
		_bnd = _img.get_band()

		_ext = geo_raster_ex.geo_polygon.from_raster(_bnd.raster)
		if _proj != None:
			_ext = _ext.project_to(_proj)

		_ftr = ogr.Feature(_lyr.GetLayerDefn())
		_ftr.SetField('file', _f)
		_ftr.SetGeometry(_ext.poly)
		_lyr.CreateFeature(_ftr)
		_ftr.Destroy()

		fzip.clean(False)

	_perc.done()

def generate_shp_from_file(fs, dataset, proj, f_out, absp, d_tmp):
	import os

	_fs = []
	for i in xrange(len(fs)):
		_p = os.path.abspath(_fs[i])
		if absp:
			_p = os.path.abspath(_p)

		if dataset:
			_p = _p + '#' + dataset

		_fs.append(_p)

	import file_unzip
	with file_unzip.file_unzip(d_tmp) as _zip:
		generate_shp(_fs, proj, f_out, _zip)

def generate_shp_from_list(f_list, dataset, proj, f_out, absp, d_tmp):
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

	import file_unzip
	_zip = file_unzip.file_unzip(d_tmp)
	try:
		generate_shp(_fs, proj, f_out, _zip)
	finally:
		_zip.clean()

def generate_shp_from_folder(fd, dataset, proj, f_out, absp, d_tmp):
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

	import file_unzip
	_zip = file_unzip.file_unzip(d_tmp)
	try:
		generate_shp(_fs, proj, f_out, _zip)
	finally:
		_zip.clean()

def usage():
	import argparse
	_p = argparse.ArgumentParser()
	_g_input = _p.add_mutually_exclusive_group(required=True)
	_g_input.add_argument('-i', '--input-file', dest='inputfile', nargs='*')
	_g_input.add_argument('-l', '--input-list', dest='inputlist')
	_g_input.add_argument('-d', '--input-folder', dest='inputfolder')

	_p.add_argument('-p', '--projection', dest='projection', type=int)
	_p.add_argument('-n', '--dataset', dest='dataset')
	_p.add_argument('-o', '--ouput-file', dest='output', required=True)
	_p.add_argument('-t', '--temp-path', dest='temp_path')
	_p.add_argument('-a', '--absolute-path', dest='absolutepath',
			action='store_true')

	return _p.parse_args()

if __name__ == '__main__':
	_opts = usage()
	if _opts.inputfile:
		generate_shp_from_file(_opts.inputfile, _opts.dataset, _opts.projection,
				_opts.output, _opts.absolutepath, _opts.temp_path)
	elif _opts.inputlist:
		generate_shp_from_list(_opts.inputlist, _opts.dataset, _opts.projection,
				_opts.output, _opts.absolutepath, _opts.temp_path)
	elif _opts.inputfolder:
		generate_shp_from_folder(_opts.inputfolder, _opts.dataset,
				_opts.projection, _opts.output, _opts.absolutepath,
				_opts.temp_path)
	else:
		print 'unknown inputs'
