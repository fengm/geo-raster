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
    _c = [int(sum([_c[_i] for _c in _cs])) for _i in xrange(4)]

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
        _rs = ccs if isinstance(ccs, dict) else self._load_color_file(ccs)
        _vs = sorted(_rs.keys())
        _cs = [map(int, list(_rs[_v]) + ([] if len(_rs[_v]) > 3 else [255])) for _v in _vs]

        self._vs = _vs
        self._rs = _rs
        self._cs = _cs

        self._color_table()
        
    def _load_qgis_colors(self, ls):
        _ls = ls[2:]
    
        _cs = {}
        _n = 0
    
        for _l in _ls:
            _vv = _l.split(',')
            if len(_vv) != 6:
                continue
    
            _cc = tuple(map(int, _vv[1:5]))
            _cs[_n] = _cc
    
            _n += 1
    
        if _n <= 0:
            raise Exception('no color entries found')
    
        return _cs

    def _load_color_file(self, f):
        import re

        _colors = {}
        with open(f) as _fi:
            _ls = _fi.read().splitlines()
            if _ls[0] == '# QGIS Generated Color Map Export File':
                return self._load_qgis_colors(_ls)
                
            for _l in _ls:
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
        _div = int(250 * 3.0 / len(_vs))

        _colors = {}
        _values = {}

        _vs.append(_vs[-1])
        for i in xrange(len(_vs) - 1):
            _a = _vs[i]
            _d = (_vs[i+1] - _vs[i]) / float(_div)

            for _n in xrange(_div):
                _v, _c = self._interpolate(_a)

                if _v not in _colors:
                    _values[_a] = _v
                    _colors[_v] = _c

                _a += _d

        self._values = _values
        self._colors = _colors

        self._v_min = min(self._values.keys())
        self._v_max = max(self._values.keys())

        if self._v_min < 0 or self._v_max >= 250:
            raise Exception('only accept value range between 0 and 250')
            
    def _to_byte_colors(self, clip=False):
        _cs = {}
        for _c in xrange(int(self._v_min), int(self._v_max) + 1):
            _cs[_c] = self.get_color(_c, clip)
            
        return _cs
            
    def write_file(self, f, clip=False):
        _ls = []
        
        _cs = self._to_byte_colors(clip)
        for _v in sorted(_cs.keys()):
            _ls.append('%s\t%s' % (_v, ','.join(map(str, _cs[_v]))))

        with open(f, 'w') as _fo:
            _fo.write('\n'.join(_ls))

    def ogr_color_table(self, clip=False):
        return map_colortable(self._to_byte_colors(clip))

    def get_code(self, v, clip=False):
        if v >= 255:
            return 255

        if v < self._v_min:
            if clip:
                return 255
            return self._values[self._v_min]
        if v > self._v_max:
            if clip:
                return 255
            return self._values[self._v_max]

        _vs = []
        for _v in self._values.keys():
            if _v == v:
                return self._values[_v]

            _vs.append({'d': abs(_v - v), 'c': self._values[_v]})

        _cc = sorted(_vs, cmp=lambda x1, x2: cmp(x1['d'], x2['d']))[0]['c']
        return _cc

    def get_color(self, v, clip=False):
        _c = self.get_code(v, clip)

        if _c >= 255 or _c not in self._colors:
            return [0, 0, 0, 0]

        return self._colors[_c]

    def _interpolate(self, v):
        _vs = self._vs
        _cs = self._cs

        _v = max(min(_vs), min(v, max(_vs) - 0.000000000001))
        _dv = float(250) / (len(_vs) - 1)

        _pp = 0.0

        for _i in xrange(len(_vs) - 1):
            _ds = abs(_v - _vs[_i])
            _ps = int(_pp)

            if _ds == 0:
                return _ps, _cs[_i]

            if _vs[_i] < _v < _vs[_i+1]:
                _vv = []

                _vv.append({'idx': _i, 'pos': _ps, 'value': _vs[_i], 'color': _cs[_i], 'dist': float(_ds)})

                _ds = abs(_v - _vs[_i + 1])
                _ps = int(_pp + _dv)
                _vv.append({'idx': _i+1, 'pos': _ps, 'value': _vs[_i+1], 'color': _cs[_i+1], 'dist': float(_ds)})

                return to_dist(_vv)
            else:
                _pp += _dv

        raise Exception('failed to find value %s' % v)

def load(f):
    return color_table(f).ogr_color_table()
