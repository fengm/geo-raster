#!/usr/bin/env python
# encoding: utf-8

class extent:

	def __init__(self, ext):
		self.minx = ext[0]
		self.miny = ext[2]
		self.maxx = ext[1]
		self.maxy = ext[3]

# def load_shp(f_shp):
# 	import fiona
#
# 	with fiona.open(f_shp, 'r') as _shp:
# 		return extent(_shp.bounds)

def create_raster(f_img, f_shp, f_out, fzip):
	from osgeo import gdal, ogr
	_shp = ogr.Open(f_shp)
	_lyr = _shp.GetLayer()

	ext = extent(_lyr.GetExtent())

	import geo_raster_c as ge

	_img = ge.geo_raster.open(fzip.unzip(f_img))
	_bnd = _img.get_band()

	_ext = list(_img.geo_transform)
	_cel = _ext[1]

	to_floor = lambda v, s, cell: int(math.floor((v - s) / float(cell)))
	to_ceil = lambda v, s, cell: int(math.ceil((v - s) / float(cell)))

	import math

	_s_x = max(0, to_floor(ext.minx, _ext[0], _cel))
	_e_x = min(_img.width, to_ceil(ext.maxx, _ext[0], _cel))

	_s_y = max(0, to_floor(_ext[3], ext.maxy, _cel))
	_e_y = min(_img.height, to_ceil(_ext[3], ext.miny, _cel))

	_cols = _e_x - _s_x
	_rows = _e_y - _s_y

	_dat = _bnd.read_rows(_s_y, _rows)[:, _s_x: _e_x]

	_ext[0] = _ext[0] + _s_x * _cel
	_ext[3] = _ext[3] - _s_y * _cel

	_f_tmp = fzip.generate_file('', '.img')
	_img_tmp = ge.geo_raster.create(_f_tmp, [_rows, _cols], _ext, _img.projection)
	_bnd_tmp = _img_tmp.get_band()

	import numpy
	_bnd_tmp.write(numpy.zeros(_dat.shape, dtype=numpy.uint8))
	gdal.RasterizeLayer(_img_tmp.raster, [1], _lyr, burn_values=[1])
	del _img_tmp, _bnd_tmp

	_img_out = ge.geo_raster.create(f_out, [_rows, _cols], _ext, _img.projection, nodata=_bnd.nodata, pixel_type=_bnd.pixel_type)
	# _img = ge.geo_raster.open(f_tmp, update=True)
	_bnd_out = _img_out.get_band()

	_ddd = ge.geo_raster.open(_f_tmp).get_band().read()
	_dat[_ddd == 0] = _bnd.nodata

	_bnd_out.write(_dat)
	del _bnd, _img, _lyr, _shp, _img_out, _bnd_out

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-s', '--shape', dest='shape', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)

	return _p.parse_args()

def main():
	_opts = usage()

	import file_unzip
	with file_unzip.file_unzip() as _zip:
		create_raster(_opts.input, _opts.shape, _opts.output, _zip)

def init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	import logging_util
	logging_util.init()

if __name__ == '__main__':
	init_env()
	main()
