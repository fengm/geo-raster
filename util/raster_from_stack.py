#!/usr/bin/env python
# encoding: utf-8

def retrieve_raster(f_img, dataset_name, f_ref, f_out, d_tmp):
	import geo_raster, geo_raster_ex

	_img = geo_raster.geo_raster.open(f_ref)
	_bnd = _img.get_band()

	import numpy
	_dat = numpy.empty((_bnd.height, _bnd.width))

	import file_unzip
	_zip = file_unzip.file_unzip(d_tmp)

	_stk = geo_raster_ex.geo_band_stack_zip.from_shapefile(f_img,
			dataset_name=dataset_name, file_unzip=_zip)
	_prj = geo_raster_ex.projection_transform.from_band(_bnd.band_info(),
			_stk.proj)

	_ddd = _stk.get_band_xy(*_prj.project(0, 0))

	import progress_percentage
	_ppp = progress_percentage.progress_percentage(_bnd.height)
	for _row in xrange(_bnd.height):
		_ppp.next()
		for _col in xrange(_bnd.width):
			_x, _y = _prj.project(_col, _row)

			_v = _stk.read_xy(_x, _y)
			_dat[_row, _col] = _v

	_ppp.done()

	geo_raster.write_raster(f_out, _img.geo_transform, _img.projection, _dat, pixel_type=_ddd.band.pixel_type)

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-r', '--refer', dest='refer', required=True)
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('-t', '--temp-path', dest='temp_path')

	return _p.parse_args()

if __name__ == '__main__':
	_opts = usage()
	retrieve_raster(_opts.input, None, _opts.refer, _opts.output, _opts.temp_path)

