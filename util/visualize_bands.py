'''
File: visualize_bands.py
Author: Min Feng
Version: 0.1
Create: 2014-04-03 16:40:03
Description: convert raster data to visualiable image
'''


def search_threshold(vs, ls, sh):
	_sum = int(sum(vs) * sh)

	_t = 0
	for i in xrange(len(vs)):
		_t += vs[i]
		if _t > _sum:
			return ls[i]

	raise Exception('failed to find threshold')

def convert_band_sr(bnd, ref, sh=0.2):
	import numpy as np

	if bnd.nodata == None:
		bnd.nodata = 0

	_bnd = bnd.cache()
	_dat = _bnd.data

	import math
	_low = math.log(150)
	_top = math.log(5000)

	_dat[_dat > 0] = (np.log(_dat.astype(np.float32)[_dat > 0]) - _low) * (256.0 / (_top - _low))

	_dat[_dat > 255] = 255
	_dat[_dat < 0] = 0

	return _bnd.from_grid(_dat, nodata=0)

def convert_band(bnd, ref, sh=0.2):
	import numpy as np
	import logging

	if bnd.nodata == None:
		bnd.nodata = 0

	_bnd = bnd.cache()
	_dat = _bnd.data_ma

	_ddd = _dat

	_min = _dat.min()
	_max = _dat.max()

	_bin = int(_max - _min)
	_bin = max(_bin, 10)

	logging.info('data range: %s, %s, %s' % (_min, _max, _bin))
	_vs, _ls = np.histogram(_ddd, bins=_bin, range=(_min, _max))

	_low = search_threshold(_vs, _ls, sh)
	_top = search_threshold(_vs[::-1], _ls[::-1], sh)

	if _top <= _low:
		raise Exception('failed to find threshold %s - %s' % (_low, _top))

	logging.info('threshold: %s - %s' % (_low, _top))

	_dat = (_dat.astype(np.float32) - _low) * (256.0 / (_top - _low))

	_dat[_dat > 255] = 255
	_dat[_dat < 0] = 0

	return _bnd.from_ma_grid(_dat, nodata=0)

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

		if len(_bnds) not in [1, 3]:
			raise Exception('Incorrect band numbers %s' % len(_bnds))

		_bnd = _bnds[0]

		_opt = []
		if _opts.output.endswith('.tif'):
			_opt.append('compress=lzw')
		if _opts.output.endswith('.img'):
			_opt.append('COMPRESS=YES')

		_img = ge.geo_raster.create(_opts.output, [len(_bnds), _bnd.height, _bnd.width],
				_bnd.geo_transform, _bnd.proj, ge.pixel_type(), opts=_opt)

		for i in xrange(len(_bnds)):
			print ' + band', _opts.bands[i]

			_bbb = _img.get_band(i + 1)
			_fun = convert_band_sr if _opts.convert_sr else convert_band
			_bbb.write(_fun(_bnds[i], _bnd).data)

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






