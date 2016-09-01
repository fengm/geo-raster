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
			_clr = ge.load_colortable(f_clr)

		_bnd.cache().save(os.path.join(_d_tmp, _f.replace('.img', '.tif').replace('.gz', '')), \
			color_table=_clr, opts=['compress=lzw'])

		file_unzip.compress_folder(_d_tmp, d_out, [])

def main():
	_opts = _init_env()

	_ls = [_opts.input] if not _opts.input.endswith('.txt') else open(_opts.input).read().strip().splitlines()

	from gio import multi_task
	_ps = [(_l, _opts.color, _opts.output) for _l in multi_task.load(_ls, _opts)]

	multi_task.run(convert_file, _ps, _opts)

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-c', '--color', dest='color')
	_p.add_argument('-o', '--output', dest='output', required=True)

	from gio import multi_task
	multi_task.add_task_opts(_p)

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

	if not config.cfg.has_section('conf'):
		config.cfg.add_section('conf')

	for _k, _v in _opts.__dict__.items():
		if _v != None:
			config.cfg.set('conf', _k, str(_v))


	from gio import file_unzip as fz
	fz.clean(fz.default_dir(_opts.temp))

	return _opts

if __name__ == '__main__':
	main()

