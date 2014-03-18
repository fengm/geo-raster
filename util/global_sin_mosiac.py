
import logging

def create_output_raster(row, col, resolution, f_out):
	_div = 1111950.5197665232305861525775064
	_c_x = (col - 36 / 2) * _div
	_c_y = (row - 18 / 2) * _div

	import math
	_cel = int(math.ceil((_div / resolution)))
	_geo = [_c_x, resolution, 0, _c_y, 0, -resolution]

	import numpy as np
	_dat = np.empty((_cel, _cel), dtype=np.int8)
	_dat.fill(255)

	import geo_raster_c as ge
	import geo_raster_ex_c as gx

	_bnd = ge.geo_band_cache(_dat, _geo, gx.modis_projection(), nodata=255)
	_bnd.write(f_out)
	# ge.geo_raster.create(f_out, [_cel, _cel], _geo, gx.modis_projection().ExportToWkt(), driver='HFA', nodata=255)

class band_obj:

	def __init__(self, poly, f, fzip):
		self.poly = poly
		self.band_file = f
		self.fzip = fzip
		self._band = None

	@property
	def band(self):
		if self._band == None:
			import geo_raster_c as ge
			_f = self.fzip.unzip(self.band_file)
			self._band = ge.geo_raster.open(_f).get_band()

		return self._band

def load_shp_file(f_shp, fzip):
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

		_bnds.append(band_obj(_poly, _file, fzip))

	if len(_bnds) == 0:
		logging.error('No images found')
		return None

	return _bnds

def process_file(bnd, ext, f):
	_ext1 = f.poly.project_to(bnd.proj).intersect(ext).extent()

	# _bnd_inp = f.band
	# import geo_base_c as gb
	# gb.output_polygons([_bnd_inp.extent().to_polygon().project_to(bnd.proj)], 'test6.shp')

	_bnd_inf = bnd.align(_ext1, True)
	if _bnd_inf.width <= 0 or _bnd_inf.height <= 0:
		logging.error('failed to estimate the union area raster %s, %s' % (_bnd_inf.width, _bnd_inf.height))
		return

	_bnd_out = f.band.read_block(_bnd_inf)

	if _bnd_out == None:
		import geo_raster_c as ge
		import numpy as np
		_bbb = ge.geo_band_cache(np.zeros((_bnd_inf.height, _bnd_inf.width), dtype=np.uint8), _bnd_inf.geo_transform, _bnd_inf.proj, 255, ge.pixel_type())
		_bbb.write('test2.img')
		import sys
		sys.exit(0)
		print ' * skip'
		return

	_geo1 = bnd.geo_transform
	_geo2 = _bnd_out.geo_transform

	import math
	_col = int(math.floor((_geo2[0] - _geo1[0]) / _geo1[1]))
	_row = int(math.floor((_geo2[3] - _geo1[3]) / _geo1[5]))

	import combine_grid
	_dat = bnd.read_rows(_row, _bnd_out.height)
	_dat = _dat[:, _col: _col + _bnd_out.width]

	assert(_dat.shape[0] == _bnd_out.data.shape[0] and _dat.shape[1] == _bnd_out.data.shape[1])
	combine_grid.combine(_dat, bnd.nodata, _bnd_out.data, _bnd_out.nodata)

	bnd.write(_dat, _col, _row)

def search_files(fs, ext):
	_fs = []
	for _f in fs:
		if _f.poly.segment_ratio(10).project_to(ext.proj).is_intersect(ext):
			_fs.append(_f)

	return _fs

def mosiac_tile(fs, bnd, ext):

	import progress_percentage
	_ppp = progress_percentage.progress_percentage(len(fs))

	for _f in fs:
		_ppp.next(count=True, message=_f.band_file)

		try:
			process_file(bnd, ext, _f)
		except KeyboardInterrupt:
			print '\n\n* User stopped the program'
		except Exception, err:
			import traceback

			logging.error(traceback.format_exc())
			logging.error(str(err))

			print '\n\n* Error:', err

	_ppp.done()

def process_task(f_inp, row, col, d_tmp, d_out):
	import file_unzip
	import os

	_f_out = d_out + '%03d_%03d.img' % (row, col)
	if os.path.exists(_f_out):
		print ' * exited'
		return

	with file_unzip.file_unzip(d_tmp) as _zip:
		print '== v%02dh%02d' % (row, col)

		print 'load shapefiles'
		_fs = load_shp_file(f_inp, _zip)
		print 'loaded %s files' % len(_fs)

		print 'create output images'
		_resolution = 120.0
		create_output_raster(row, col, _resolution, _f_out)

		import geo_raster_c as ge
		_bnd_img = ge.geo_raster.open(_f_out, True).get_band()
		_ext_img = _bnd_img.extent().to_polygon()

		_ff = search_files(_fs, _ext_img)
		if len(_ff) == 0:
			print ' * skip because of no image'
			import os
			os.remove(_f_out)
			return

		print 'start mosaic'
		mosiac_tile(_ff, _bnd_img, _ext_img)

def main():
	_opts = _init_env()

	_fs = []
	for _row in xrange(36 / 2):
		for _col in xrange(36):
			# if _row != 5 or _col != 12:
			# 	continue

			_fs.append((_opts.input, _row, _col, _opts.temp, _opts.output))

	import multi_task
	_fs = multi_task.load_list_opts(_fs, _opts)

	_p = multi_task.Pool(process_task, _fs, _opts.task_num)
	_p.run()

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')

	_p.add_argument('-t', '--temp', dest='temp')
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)

	import multi_task
	multi_task.add_task_opts(_p)

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

	if os.path.exists(_opts.temp):
		import shutil
		shutil.rmtree(_opts.temp)

	return _opts

if __name__ == '__main__':
	main()

