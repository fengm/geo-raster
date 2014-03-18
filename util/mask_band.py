#!/usr/bin/env python
# encoding: utf-8

'''
File: mask_band.py
Author: Min Feng
Version: 0.1
Create: 2013-06-05 18:46:51
Description: exclude pixels from the target band where the value of given pixel is
	one of values from the refer band
'''

def mask_band(f_img, f_ref, exclude_vs, f_out):
	import geo_raster_c as ge

	_bnd_d = ge.geo_raster.open(f_img).get_band().cache()
	_bnd_r = ge.geo_raster.open(f_ref).get_band().cache()

	assert(_bnd_d.nodata)
	assert(_bnd_r.height == _bnd_d.height and _bnd_r.width == _bnd_d.width)

	_dat_d = _bnd_d.data
	_dat_r = _bnd_r.data

	for _v in exclude_vs:
		print 'exclude', _v
		_dat_d[_dat_r == _v] = _bnd_d.nodata

	_bnd_d.write(f_out)

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-r', '--refer', dest='refer', required=True)
	_p.add_argument('-e', '--exclude-value', dest='exclude_value', required=True, type=int, nargs='+')
	_p.add_argument('-o', '--output', dest='output', required=True)

	return _p.parse_args()

def main():
	_opts = usage()
	mask_band(_opts.input, _opts.refer, _opts.exclude_value, _opts.output)

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
