#!/usr/bin/env python
# encoding: utf-8

def stat_band(f_in, value_bin, value_range, f_ot, density):
	import geo_raster_c as ge

	_bnd = ge.geo_raster.open(f_in).get_band().cache()
	_dat = _bnd.data

	import numpy as np
	_hist, _bins = np.histogram(_dat, value_bin, value_range, normed=False)

	_sum = float(sum(_hist))
	_ls = ['max_value,text,stat,stat_norm']
	for i in range(len(_hist)):
		_ls.append('%s,%s-%s,%s,%f' % (_bins[i+1], _bins[i], _bins[i+1], _hist[i], _hist[i] / _sum))

	with open(f_ot, 'w') as _f:
		_f.write('\n'.join(_ls))

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-b', '--bins', dest='bins', required=True, type=int)
	_p.add_argument('-r', '--range', dest='range', required=True, type=float, nargs=2)
	_p.add_argument('-o', '--output', dest='output')
	# _p.add_argument('-d', '--density', dest='density', default=False, action='store_true')

	return _p.parse_args()

def init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	import logging_util
	logging_util.init()

if __name__ == '__main__':
	init_env()
	_opts = usage()

	import file_unzip
	with file_unzip.file_unzip('tmp') as _zip:
		_f_in = _zip.unzip(_opts.input)

		if not _opts.output:
			_opts.output = (_f_in[:-4] if _f_in[-4:] in ['.tif', '.img'] else _f_in) + '.csv'
			if _f_in != _opts.input:
				import os
				_opts.output = os.path.join(os.path.dirname(_opts.input), os.path.basename(_opts.output))

		# stat_band(_f_in, _opts.bins, _opts.range, _opts.output, _opts.density)
		stat_band(_f_in, _opts.bins, _opts.range, _opts.output, True)


