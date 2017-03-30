#!/usr/bin/env python
# encoding: utf-8

'''
File: convert_to_geotiff.py
Author: Min Feng
Version: 0.1
Create: 2016-09-01 11:33:00
Description: convert images to GeoTIFF format
'''

def convert_file(f_img, f_clr, d_out):
	from gio import file_unzip
	with file_unzip.file_unzip() as _zip:
		import os

		_d, _f = os.path.split(f_img)
		_d_tmp = _zip.generate_file()
		os.path.exists(_d_tmp) or os.makedirs(_d_tmp)

		from gio import geo_raster as ge
		_bnd = ge.open(_zip.unzip(f_img)).get_band()

		_clr = _bnd.color_table
		if f_clr:
			# from gio import color_table
			# _clr = color_table.color_table(f_clr).ogr_color_table()
			_clr = ge.load_colortable(f_clr)

		_bnd.cache().save(os.path.join(_d_tmp, _f.replace('.img', '.tif').replace('.gz', '')), \
			color_table=_clr, opts=['compress=lzw'])

		file_unzip.compress_folder(_d_tmp, d_out, [])

def main(opts):
	_ls = [opts.input] if not opts.input.endswith('.txt') else open(opts.input).read().strip().splitlines()

	from gio import multi_task
	_ps = [(_l, opts.color, opts.output) for _l in multi_task.load(_ls, opts)]

	multi_task.run(convert_file, _ps, opts)

def usage():
	_p = environ_mag.usage(True)

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-c', '--color', dest='color')
	_p.add_argument('-o', '--output', dest='output', required=True)

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])


