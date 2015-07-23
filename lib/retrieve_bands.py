#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: retrieve_bands.py
Author: Min Feng
Version: 0.1
Create: 2014-04-03 19:04:22
Description:
'''

def main():
	_opts = _init_env()

	import file_unzip
	with file_unzip.file_unzip(_opts.temp) as _zip:
		import geo_raster_c as ge

		print 'loading', _opts.input

		_bnds = []
		_f_in = _zip.unzip(_opts.input)

		if _f_in.endswith('hdf'):
			_img = ge.geo_raster.open(_f_in)

			for _b in _opts.bands:
				_bnds.append(_img.get_subdataset(_b).get_band())
		else:
			_img = ge.geo_raster.open(_f_in)

			for _b in _opts.bands:
				_bnds.append(_img.get_band(int(_b)))

		if len(_bnds) == 0:
			raise Exception('Incorrect band numbers %s' % len(_bnds))

		_bnd = _bnds[0]

		_opt = []
		if _opts.output.endswith('.tif'):
			_opt.append('compress=lzw')
		if _opts.output.endswith('.img'):
			_opt.append('COMPRESS=YES')

		_img = ge.geo_raster.create(_opts.output, [len(_bnds), _bnd.height, _bnd.width],
				_bnd.geo_transform, _bnd.proj, _bnd.pixel_type, opts=_opt)

		for i in xrange(len(_bnds)):
			print ' + band', _opts.bands[i]

			_bbb = _img.get_band(i + 1)
			_bbb.write(_bnds[i].cache().data)

		_img = None

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-b', '--bands', dest='bands', required=True, nargs='+')
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('-sr', '--convert-sr', dest='convert_sr', action='store_true')

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

	import file_unzip as fz
	fz.clean(fz.default_dir(_opts.temp))

	return _opts

if __name__ == '__main__':
	main()






