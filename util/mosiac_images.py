'''
File: global_con_mosiac.py
Author: Min Feng
Version: 0.1
Create: 2014-03-04 19:44:24
Description: Mosaic images into a single file
'''
import logging

def fill_raster(f_img):
	import geo_raster_c as ge

	_bnd = ge.geo_raster.open(f_img, True).get_band()
	_row_s = 100

	import progress_percentage
	_ppp = progress_percentage.progress_percentage(_bnd.height, title='initialize raster')

	for _row in xrange(0, _bnd.height, _row_s):
		_ppp.next(_row_s)

		_dat = _bnd.read_rows(_row, _row_s)
		_dat.fill(_bnd.nodata)
		_bnd.write(_dat, 0, _row)

	_ppp.done()

def create_output_raster(f_shp, col_name, col_text, resolution, proj, nodata, f_out):
	from osgeo import ogr
	_shp = ogr.Open(f_shp)
	_lyr = _shp.GetLayer()

	import geo_raster_c as ge
	_prj = ge.proj_from_epsg()
	_prj.ImportFromProj4(proj)

	_use_col = False
	if col_name and col_text:
		_use_col = True

		print 'select %s=%s' % (col_name, col_text)

		_c_name = None
		_cs = []
		for _c in _lyr.schema:
			if _c.name.upper() == col_name.upper():
				_c_name = _c.name
				col_name = _c_name
				break
			_cs.append(_c.name)

		if _c_name == None:
			raise Exception('failed to find the column (%s) (%s)' % (col_name, ', '.join(_cs)))

		col_text = col_text.strip()

	else:
		print ' * use all the features'

	_fs = []
	_ex = None
	import geo_base_c as gb
	for _f in _lyr:
		if not _use_col:
			_ge = gb.geo_polygon(_f.geometry().Clone()).project_to(_prj)
			if _ge != None:
				_fs.append(_ge)
				if _ex == None:
					_ex = _ge.extent()
				else:
					_ex = _ex.union(_ge.extent())
		else:
			_n = str(_f.items()[col_name]).strip()
			if _n == col_text:
				_ge = gb.geo_polygon(_f.geometry().Clone()).project_to(_prj)
				if _ge != None:
					_fs.append(_ge)
					if _ex == None:
						_ex = _ge.extent()
					else:
						_ex = _ex.union(_ge.extent())

	print 'found %s features' % len(_fs)
	if len(_fs) <= 0:
		raise Exception('failed to find any record')

	import math
	_rows = int(math.ceil(_ex.width() / resolution))
	_cols = int(math.ceil(_ex.height() / resolution))

	logging.info(' - %s x %s (%s) nodata: %s' % (_cols, _rows, resolution, nodata))
	print ' - %s x %s (%s) nodata: %s' % (_cols, _rows, resolution, nodata)

	_geo = [_ex.minx, resolution, 0, _ex.maxy, 0, -resolution]
	ge.geo_raster.create(f_out, [_cols, _rows], _geo, _prj, driver='HFA', nodata=nodata)

	# initialize the raster
	if nodata != 0:
		print 'fill the output raster (%s)' % nodata
		fill_raster(f_out)

	return _fs

class band_obj:

	def __init__(self, poly, f):
		self.poly = poly
		self.band_file = f

def load_shp_file(f_shp):
	from osgeo import ogr

	_shp = ogr.Open(f_shp)
	if _shp == None:
		raise Exception('Failed to load shapefile ' + f_shp)

	_lyr = _shp.GetLayer()

	import os
	_d_shp = os.path.dirname(f_shp)

	_file_columns = [_col.name for _col in _lyr.schema if _col.name.lower() == 'file']
	if len(_file_columns) != 1:
		raise Exception('failed to find the FILE column in the shapefile (%s)' % ','.join([_col.name for _col in _lyr.schema]))

	_bnds = []
	import geo_base_c as gb
	for _f in _lyr:
		_poly = gb.geo_polygon(_f.geometry().Clone())
		_file = _f.items()[_file_columns[0]]

		if not (_file[0] == '/' or _file[1] == ':'):
			# handle relative path
			_file = _d_shp + os.sep + _file

		_bnds.append(band_obj(_poly, _file))

	if len(_bnds) == 0:
		logging.error('No images found')
		return None

	return _bnds

def process_file(bnd, ext, f, fzip, lock=None):
	logging.info('opening input file %s' % f)

	import geo_raster_c as ge
	_bnd_inp = ge.geo_raster.open(fzip.unzip(f)).get_band()

	_ext1 = _bnd_inp.extent().to_polygon().segment_ratio(5).project_to(bnd.proj).intersect(ext).extent()

	# _bnd_inp = f.band
	# import geo_base_c as gb
	# gb.output_polygons([_bnd_inp.extent().to_polygon().project_to(bnd.proj)], 'test6.shp')

	_bnd_inf = bnd.align(_ext1, True)
	if _bnd_inf.width <= 0 or _bnd_inf.height <= 0:
		logging.error('failed to estimate the union area raster %s, %s' % (_bnd_inf.width, _bnd_inf.height))
		return

	logging.info('reading input block (%s)' % f)
	_bnd_out = _bnd_inp.read_block(_bnd_inf)

	if _bnd_out == None:
		logging.warning('skip the file %s' % f)
		return

	_geo1 = bnd.geo_transform
	_geo2 = _bnd_out.geo_transform

	import math
	_col = int(math.floor((_geo2[0] - _geo1[0]) / _geo1[1]))
	_row = int(math.floor((_geo2[3] - _geo1[3]) / _geo1[5]))

	import combine_grid
	logging.info('reading target block')

	if lock == None:
		import threading
		lock = threading.Lock()

	with lock:
		logging.info('start lock')
		_dat = bnd.read_rows(_row, _bnd_out.height, _col, _bnd_out.width)

		logging.info('combine pixels')
		# _dat = _dat[:, _col: _col + _bnd_out.width]
		assert(_dat.shape[0] == _bnd_out.data.shape[0] and _dat.shape[1] == _bnd_out.data.shape[1])
		logging.info('band nodata: %s, output nodata: %s' % (bnd.nodata, _bnd_out.nodata))
		combine_grid.combine(_dat, bnd.nodata, _bnd_out.data, _bnd_out.nodata)

		logging.info('write target block %s' % f)
		bnd.write(_dat, _col, _row)
		logging.info('end writing %s' % f)
		logging.info('end lock')

def search_files(fs, ps):
	_ps = []
	for _p in ps:
		_ps.append(_p.project_to(fs[0].poly.proj))

	print 'search for files'
	import progress_percentage
	_ppp = progress_percentage.progress_percentage(len(fs))

	_fs = []
	for _f in fs:
		_ppp.next()

		for _p in _ps:
			if _f.poly.is_intersect(_p):
				_fs.append(_f)
				break

	_ppp.done()

	return _fs

def mosiac_tile_task(f, f_img, d_tmp, lock):
	import geo_raster_c as ge
	_bnd_img = ge.geo_raster.open(f_img, True).get_band()
	_ext_img = _bnd_img.extent().to_polygon()

	import file_unzip

	with file_unzip.file_unzip(d_tmp) as _zip:
		try:
			process_file(_bnd_img, _ext_img, f, _zip, lock)
		except KeyboardInterrupt, _err:
			print '\n\n* User stopped the program'
			raise _err

		except Exception, err:
			import traceback

			logging.error(traceback.format_exc())
			logging.error(str(err))

			print '\n\n* Error:', err

def process_task(f_inp, f_con, col_name, col_text, resolution, srs, nodata, d_tmp, d_out, task_num):
	import os

	_f_out = d_out
	# if os.path.exists(_f_out):
	# 	print ' * exited'
	# 	return

	print 'load shapefiles'
	_fs = load_shp_file(f_inp)
	print 'loaded %s files' % len(_fs)

	print 'create output images'
	_ps = create_output_raster(f_con, col_name, col_text, resolution, srs, nodata, _f_out)

	_ff = search_files(_fs, _ps)
	if len(_ff) == 0:
		print ' * skip because of no image'
		os.remove(_f_out)
		return

	print 'find %s' % len(_ff)

	print 'start mosaic'
	print 'run multitask:', task_num

	_ps = []
	for _f in _ff:
		for _i in _f.band_file.split(','):
			_ps.append((_i, _f_out, d_tmp))

	import multi_task
	_pool = multi_task.Pool(mosiac_tile_task, _ps, task_num)
	_pool.run([_pool.create_lock()])

def main():
	_opts = _init_env()

	from osgeo import gdal
	gdal.UseExceptions()

	process_task(_opts.input, _opts.extent_shp, _opts.column_name, _opts.column_text, _opts.resolution, _opts.srs, _opts.nodata, _opts.temp, _opts.output, _opts.task_num)

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')

	_p.add_argument('-t', '--temp', dest='temp')
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('--column-name', dest='column_name')
	_p.add_argument('--column-text', dest='column_text')
	_p.add_argument('-s', '--srs', dest='srs', required=True)
	_p.add_argument('-r', '--resolution', dest='resolution', type=float, required=True)
	_p.add_argument('--extent-shp', dest='extent_shp', required=True)
	_p.add_argument('--nodata', dest='nodata', type=int, default=255)
	_p.add_argument('-ts', '--task-num', dest='task_num', type=int, default=1)

	return _p.parse_args()

def _init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	_opts = _usage()

	import logging_util
	logging_util.init(_opts.logging)

	import config
	config.load(_opts.config)

	if _opts.temp and os.path.exists(_opts.temp):
		import shutil
		shutil.rmtree(_opts.temp)

	return _opts

if __name__ == '__main__':
	main()

