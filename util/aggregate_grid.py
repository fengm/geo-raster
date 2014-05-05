
def resize_band(bnd, res, f_out):
	_geo = list(bnd.geo_transform)

	_div = res / _geo[1]
	for _idx in range(6):
		if _idx in (0, 3):
			continue
		_geo[_idx] *= _div

	_rows = int(bnd.height / _div)
	_cols = int(bnd.width / _div)
	print 'output grid size: ', _cols, _rows

	import geo_raster_c as ge
	ge.geo_raster.create(f_out, [_rows, _cols], _geo, bnd.proj, bnd.pixel_type, nodata=bnd.nodata)

	_img = ge.open(f_out, True)
	return _img.get_band()
	# return ge.geo_band_info(_geo, _cols, _rows, bnd.proj, bnd.nodata, bnd.pixel_type)

def aggregate(f_img, res, f_out):
	import geo_raster_c as ge
	import aggregate_band as ag

	_bnd_inp = ge.open(f_img).get_band()
	_bnd_out = resize_band(_bnd_inp, res, f_out)

	_div = 100

	import progress_percentage
	_ppp = progress_percentage.progress_percentage(_bnd_out.height)

	for _row in xrange(0, _bnd_out.height, _div):
		_ppp.next(_div)

		_bnd_inf = _bnd_out.sub_band(0, _row, _bnd_out.width, _div)
		_bnd_ext = _bnd_inp.align(_bnd_inf.extent(), True)
		_bnd_sub = _bnd_inp.read_block(_bnd_ext)
		_bnd_agg = ag.mean(_bnd_sub, _bnd_inf)
		_bnd_out.write(_bnd_agg.data, 0, _row)

	_ppp.done()

def main():
	_opts = _init_env()
	aggregate(_opts.input, _opts.resolution, _opts.output)

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-r', '--resolution', dest='resolution', required=True, type=float)
	_p.add_argument('-o', '--output', dest='output', required=True)

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


