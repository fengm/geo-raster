'''
File: color_table.py
Author: Min Feng
Version: 0.1
Create: 2016-10-21 18:43:37
Description:
'''

import logging

def map_colortable(cs):
    from osgeo import gdal

    _color_tables = gdal.ColorTable()
    for i in range(256):
        if i in cs:
            _color_tables.SetColorEntry(i, tuple(cs[i] if len(cs[i]) >= 4 else (list(cs[i]) + [255])))

    _color_tables.SetColorEntry(255, (0,0,0,0))
    return _color_tables

class color_table:

    def __init__(self, ccs):
        _rs = self._load(ccs)
        
        for _r, _v in _rs.items():
            if len(_v) == 3:
                _rs[_r] = list(_v) + [255]
                
        self._colors = _rs
    
    def _load(self, ccs):
        if isinstance(ccs, dict):
            return ccs
            
        if isinstance(ccs, str):
            return self._load_color_file(ccs)
            
        from osgeo import gdal
        if isinstance(ccs, gdal.ColorTable):
            _cs = {}
            for _c in range(ccs.GetCount()):
                _cs[_c] = ccs.GetColorEntry(_c)
                
            return _cs
            
        raise Exception('failed to parse the colortable %s' % ccs)
            
    def _load_qgis_colors(self, ls):
        _ls = ls[2:]
    
        _cs = {}
        _n = 0
    
        for _l in _ls:
            _vv = _l.split(',')
            if len(_vv) != 6:
                continue
    
            _cc = tuple(map(int, _vv[1:5]))
            _cs[float(_vv[0])] = _cc
    
            _n += 1
    
        if _n <= 0:
            raise Exception('no color entries found')
    
        return _cs

    def _load_color_file(self, f):
        import re
        from gio import file_mag

        _colors = {}
        with open(file_mag.get(f).get()) as _fi:
            _ls = _fi.read().strip().splitlines()
            if len(_ls) == 0:
                raise Exception('color table is empty')

            if f.endswith('.csv') or 'QGIS' in _ls[0]:
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

    def write(self, f):
        _ls = []
        
        _cs = self._colors
        for _v in sorted(_cs.keys()):
            _ls.append('%s\t%s' % (_v, ','.join(map(str, _cs[_v]))))
        
        from gio import file_unzip
        with file_unzip.zip() as _zip:
            _zip.save('\n'.join(_ls), f)
            
    def colors(self):
        return self._colors

    def ogr_color_table(self):
        return map_colortable(self._colors)
        
class color_mapping:
    
    def __init__(self, cls, interpolate=False, clip=False, color_num=255):
        self._inp_colors = cls
        self._clip = clip
        self._color_num = color_num
        
        self._gen_color_table(self._inp_colors.colors(), interpolate)
    
    def _gen_color_table(self, rs, interpolate):
        import math
        
        _vs = list(sorted(rs.keys()))
        # _cs = [rs[_v] for _v in _vs]
        
        _colors = {}
        _values = {}

        _num = self._color_num
        if not interpolate or len(_vs) >= _num or len(_vs) < 2:
            for _r in _vs:
                _values[_r] = _r
                _colors[_r] = rs[_r]
                
        else:
            _div = float(_num - 1) / (len(_vs) - 1)
            _pos = 0
            
            for i in range(len(_vs) - 1):
                _z = (_vs[i+1] - _vs[i])
                if _z <= 0:
                    continue
                
                _u = math.floor(_div)
                _d = _z / _u
                _a = _vs[i]
                
                for _n in range(int(_u)):
                    # _v, _c = self._interpolate(_vs, _cs, _a, _num, _div)
                    _v, _c = self._interpolate_s(_vs[i], _vs[i+1], rs, _a, _pos)
                    
                    if _v > 0:
                        _values[round(_a, 7)] = _pos
                        _colors[_pos] = _c
                        
                        _pos = _v + _pos
    
                    _a += _d
                    
            _values[round(_a, 7)] = _pos
            _colors[_pos] = rs[_vs[-1]]
            
            _colors[255] = [0, 0, 0, 0]
            
        self._values = _values
        self._colors = color_table(_colors)

        self._v_min = min(self._values.keys())
        self._v_max = max(self._values.keys())

    def _to_dist_s(self, vs):
        _w = float(sum([_v['dist'] for _v in vs]))
        
        _cs = []
        for _v in vs:
            _w1 = (1.0 - _v['dist'] / _w)
            _cs.append([_w1 * _c for _c in _v['color']])
        
        _c = [int(sum([_c[_i] for _c in _cs])) for _i in range(4)]
        return _c

    def _interpolate_s(self, v_min, v_max, cs, v, n):
        if v >= v_max:
            print(v, v_max)
            raise Exception('higher than the upper range')
        
        if v <= v_min:
            return 1, cs[v_min]
            
        _vv = []
        _ds = abs(v - v_min)
        if _ds < 0.00000000001:
            return 1, cs[v_min]

        _vv.append({'color': cs[v_min], 'dist': float(_ds)})
        _vv.append({'color': cs[v_max], 'dist': float(abs(v - v_max))})

        return 1, self._to_dist_s(_vv)

    def get_code(self, v):
        if v < self._v_min:
            if self._clip:
                return 255
            return self._values[self._v_min]
            
        if v > self._v_max:
            if self._clip:
                return 255
            return self._values[self._v_max]

        _vs = []
        for _v in list(self._values.keys()):
            if _v == v:
                return self._values[_v]

            _vs.append({'d': abs(_v - v), 'c': self._values[_v]})

        _cc = sorted(_vs, key=lambda x: x['d'])[0]['c']
        return _cc

    def get_color(self, v):
        _c = self.get_code(v)

        if _c >= 255 or _c not in self._colors._colors:
            return [0, 0, 0, 0]

        return self._colors._colors[_c]
    
def load(f):
    return color_table(f).ogr_color_table()
    