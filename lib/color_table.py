'''
File: color_table.py
Author: Min Feng
Version: 0.1
Create: 2016-10-21 18:43:37
Description:
'''

import logging

def to_dist(vs):
	_w = float(sum([_v['dist'] for _v in vs]))

	_ps = []
	_cs = []

	for _v in vs:
		_w1 = (1.0 - _v['dist'] / _w)

		_ps.append(_w1 * _v['pos'])
		_cs.append([_w1 * _c for _c in _v['color']])

	_p = int(sum(_ps))
	_c = [int(sum([_c[_i] for _c in _cs])) for _i in xrange(3)]

	return _p, _c

def map_colortable(cs):
	from osgeo import gdal

	_color_tables = gdal.ColorTable()
	for i in xrange(256):
		if i in cs:
			_color_tables.SetColorEntry(i, tuple(cs[i] if len(cs[i]) >= 4 else (list(cs[i]) + [255])))

	_color_tables.SetColorEntry(255, (0,0,0,0))
	return _color_tables

class color_table:

	def __init__(self, ccs):
		_vs = sorted(ccs.keys()) if isinstance(ccs, dict) else self._load_color_file(ccs)

		_rs = []
		_dv = float(255) / (len(_vs) - 1)
		_pp = 0.0

		for _i in xrange(len(_vs) - 1):
			_ps = int(_pp)
			_pp += _dv

			_rs.append({'idx': _i, 'pos': _ps, 'value': _vs[_i], 'color': self._color(ccs[_vs[_i]])})

		self._vs = _vs
		self._rs = _rs

	def _load_color_file(self, f):
		import re

		_colors = {}
		with open(f) as _fi:
			for _l in _fi.read().splitlines():
				_l = _l.strip()
				if not _l:
					continue

				_vs = re.split('\s+', _l, maxsplit=1)
				if len(_vs) != 2:
					logging.warning('ignore color entry: %s' % _l)
					continue

				_cs = tuple([int(_v) for _v in re.split('\W+', _vs[1])])
				if len(_cs) < 3:
					raise Exception('insufficent color values %s' % len(_cs))
				_colors[float(_vs[0])] = _cs

		return _colors

	def _color(self, c):
		if len(c) < 3:
			raise Exception('insufficant color values %s' % c)

		_c = list(c)
		if len(c) == 3:
			_c.append(255)

		return tuple(_c)

	def _color_table(self):
		_vs = self._vs
		_div = int(256 * 2.0 / len(_vs))

		_colors = {}
		_values = {}
		for i in xrange(len(_vs) - 1):
			_a = _vs[i]
			_d = (_vs[i+1] - _vs[i]) / float(_div)

			for _n in xrange(_div):
				_v, _c = self._interpolate(_a)

				if _v not in _colors:
					_values[_a] = _c
					_colors[_v] = _c

				_a += _d

		self._values = _values
		self._colors = _colors

	def ogr_color_table(self):
		return map_colortable(self._colors)

	def get_color(self, v):
		_vs = []
		for _v, _c in self._values.keys():
			if _v == v:
				return _c

			_vs.append({'d': abs(_v - v), 'c': _c})
		return sorted(_vs, cmp=lambda x1, x2: cmp(x1['d'], x2['d']))[0]

	def _interpolate(self, v):
		_vs = self._vs
		_rs = self._rs

		_v = max(min(_vs), min(v, max(_vs) - 0.000000000001))

		for _i in xrange(len(_vs) - 1):
			_ds = abs(_v - _vs[_i])

			if _ds == 0:
				return _rs[_i]['pos'], _rs[_i]['color']

			if _vs[_i] < _v < _vs[_i+1]:
				_vs = []

				_vs.append([{'pos': _rs[_i]['pos'], 'dist': _rs[_i]['color'], 'dist': float(_ds)}])

				_ds = abs(_v - _vs[_i + 1])
				_vs.append([{'pos': _rs[_i+1]['pos'], 'dist': _rs[_i+1]['color'], 'dist': float(_ds)}])

				return to_dist(_vs)

		raise Exception('failed to find value %s' % v)

