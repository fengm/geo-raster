#!/usr/bin/env python
# -*- coding: utf-8 -*-

def smooth_profile(vals, div):
	_vals = [_v for _v in vals]

	for i in xrange(len(vals)):
		_i_s = max(min(len(vals), i - div), 0)
		_i_e = max(min(len(vals), i + div + 1), 0)

		_vals[i] = sum(vals[_i_s: _i_e]) / (_i_e - _i_s)

	return _vals

def stat_band(f_in, value_bin, value_range, f_ot, density, exclude_empty, smooth=0):
	import geo_raster_c as ge

	_bnd = ge.geo_raster.open(f_in).get_band().cache()
	_dat = _bnd.data_ma

	_value_range = value_range if value_range != None else (_dat.min(), _dat.max())

	import math
	_len = int(math.ceil((_value_range[1] - _value_range[0]) / value_bin))
	_value_range[1] = _value_range[0] + _len * value_bin

	print 'range: %s - %s' % tuple(_value_range)
	print 'bins:', _len

	import numpy as np
	_hist, _bins = np.histogram(_dat, _len, _value_range, normed=False)
	if smooth > 0:
		_hist = smooth_profile(_hist, smooth)

	_sum = float(sum(_hist))
	_ls = ['max_value,text,stat,stat_norm']
	for i in range(len(_hist)):
		if exclude_empty and _hist[i] == 0:
			continue

		_ls.append('%s,%s ~ %s,%s,%f' % (_bins[i], _bins[i], _bins[i+1], _hist[i], _hist[i] / _sum))

	with open(f_ot, 'w') as _f:
		_f.write('\n'.join(_ls))

def main():
	_opts = _init_env()

	import file_unzip
	with file_unzip.file_unzip(_opts.temp) as _zip:
		_f_in = _zip.unzip(_opts.input)

		if not _opts.output:
			_opts.output = (_f_in[:-4] if _f_in[-4:] in ['.tif', '.img'] else _f_in) + '.csv'
			if _f_in != _opts.input:
				import os
				_opts.output = os.path.join(os.path.dirname(_opts.input), os.path.basename(_opts.output))

		# stat_band(_f_in, _opts.bins, _opts.range, _opts.output, _opts.density)
		stat_band(_f_in, _opts.bins, _opts.range, _opts.output, True, _opts.exclude_empty, _opts.smooth)

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-b', '--bin-width', dest='bins', type=int, default=1)
	_p.add_argument('-r', '--range', dest='range', type=float, nargs=2)
	_p.add_argument('-e', '--exclude-empty', dest='exclude_empty', action='store_true')
	_p.add_argument('-s', '--smooth', dest='smooth', type=int, default=0)

	_p.add_argument('-o', '--output', dest='output')

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

