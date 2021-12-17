'''
File: cal_metrics.py
Author: Min Feng
Version: 0.1
Create: 2014-01-03 11:12:17
Description: Calcuating the statistic metrics metrics
'''
# updated (2014-01-03 11:12:29): updated the code

import logging

def cal_error_bound_2d(x, y, scale):
	'''
	calculate error budget based on x time of the Landsat and MODIS values
	squrt(quad(0.005 + 0.05 * landsat) + quad(0.005 + 0.05 * modis))
	'''
	_count = 0
	for i in range(len(x)):
		_x = x[i]
		_y = y[i]

		_err_x = (0.005 + 0.05 * _x)
		_err_y = (0.005 + 0.05 * _y)
		_err_a = scale * (((_err_x ** 2) + (_err_y ** 2)) ** 0.5)

		if _y > _x - _err_a and _y < _x + _err_a:
			_count += 1

	return float(_count) / len(x)

def cal_error_bound(x, y, scale):
	'''calculate error budget based on x time of MODIS value'''

	_count = 0
	for i in range(len(x)):
		_x = x[i]
		_y = y[i]

		_err = scale * (0.005 + 0.05 * _x)

		if _y > _x - _err and _y < _x + _err:
			_count += 1

	return float(_count) / len(x)

def cal_RMSD_SP(x, y):
	'''calculate RMSD SP'''

	_t = 0
	for i in range(len(x)):
		_t += (0.005+0.5*x[i])**2 + (0.005+0.5*y[i])**2

	return (_t / len(x)) ** 0.5

def cal_MBE(xs, ys):
	'''calcualte MBE, returns MBE (mean bias error) and S2d (distribution of differences)'''

	_t = 0
	for i in range(len(xs)):
		_t += (xs[i] - ys[i])

	_t /= len(xs)

	_s = 0
	for i in range(len(xs)):
		_s += (xs[i] - ys[i] - _t) ** 2

	_s /= len(xs) - 1

	return _t, _s

def cal_RMSD(x, y):
	'''calculate RMSD'''

	_v = 0
	for i in range(len(x)):
		_v += (x[i] - y[i]) ** 2

	return _v ** 0.5

def cal_RMSDs(x, y, slope, offset):
	'''return RMSD RMSDs RMSDu'''

	_s = 0
	_u = 0
	for i in range(len(x)):
		_p = x[i] * slope + offset

		_s += (x[i] - _p) ** 2
		_u += (y[i] - _p) ** 2

	_s /= len(x)
	_u /= len(x)

	return (_s + _u) ** 0.5, _s ** 0.5, _u ** 0.5

def average(x):
	return sum(x) / len(x)

def float_columns(cs, scale=1.0, min_v=None, max_v=None):
	_ts = [[] for _v in range(len(cs))]

	_len = min([len(_vs) for _vs in cs])

	for i in range(_len):
		try:
			_vs = [float(cs[_b][i]) * scale for _b in range(len(cs))]

			if min_v != None and any([_v < min_v for _v in _vs]):
					continue

			if max_v != None and any([_v > max_v for _v in _vs]):
				continue

			for i in range(len(_vs)):
				_ts[i].append(_vs[i])

		except ValueError:
			continue

	return _ts

def float_column(vs, scale=1.0, min_v=None, max_v=None):
	return float_columns([vs], scale, min_v, max_v)[0]

def load_columns(f, sep=',', has_header=True, columns=None, callback=None):
	'''load the values from a text file. If the file include a header line, return a dict; otherwise, return a column list'''
	_cs = None
	_ts = None
	_ss = None

	with open(f) as _fi:
		_no = 0
		for _l in _fi.read().splitlines():
			_no += 1
			if not _l:
				continue

			_vs = _l.split(sep)
			if _cs == None:
				_cs = [[] for _v in _vs]

				if has_header:
					_ts = _vs
				else:
					_ts = list(range(len(_cs)))

				if columns:
					_ss = [_ts.index(_c) for _c in columns if _c in columns]

				if has_header:
					continue

			if len(_vs) < len(_cs):
				logging.warning('insufficent values at line %s' % _no)
				continue

			if callback:
				if callback(_no, _ts, _vs) == False:
					continue

			for i in range(len(_vs)):
				if (_ss == None) or (i in _ss):
					_cs[i].append(_vs[i])

		logging.info('process %s lines' % _no)

	if _cs == None:
		logging.warning('no values loaded')
		return None

	if columns:
		for _c in [_c for _c in _ts if _c not in columns]:
			_id = _ts.index(_c)
			assert(_id >= 0)

			del _ts[_id], _cs[_id]

	return dict(list(zip(_ts, _cs)))

