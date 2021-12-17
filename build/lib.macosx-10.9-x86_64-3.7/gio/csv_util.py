'''
File: csv_util.py
Author: Min Feng
Version: 0.1
Create: 2012-06-14 18:58:28
Description: read CSV files
'''

def estimate_type(vals):
    import re

    _vs = [x == '' or re.match('^-?[0-9]+$', x) != None for x in vals]
    if False not in _vs:
        return 'int', 4

    _vs = [x == '' or x == 'NaN' or \
            re.match('^-?\d*\.?\d+E-?\d+$', x) != None or \
            re.match('^-?\d*\.?\d+$', x) != None for x in vals]
    if False not in _vs:
        return 'float', 4

    _vs = [x == '' or re.match('^-?\d*\.?\d+E-?\d+$', x) != None for x in vals]
    if False not in _vs:
        return 'float', 4

    return 'string', max(list(map(len, vals)))

def read(f, sep=','):
    import builtins
    _ls = [_l for _l in builtins.open(f, 'r').read().splitlines() if _l]

    _cols = _ls[0].split(sep)
    _vals = [_v for _v in [_l.split(sep) for _l in _ls[1:]] if len(_v) == len(_cols)]

    for _l in _ls[1:]:
        if len(_l.split(',')) != len(_cols):
            print('****', len(_l.split(',')), len(_cols), '|', _l)

    _typs = []
    for i in range(len(_cols)):
        _typs.append(estimate_type([_v[i] for _v in _vals]))

    return _cols, _typs, _vals

class csv_class:

    def __init__(self, path, cols, sep):
        self.path = path
        self.cols = cols
        self.sep = sep

    def __str__(self):
        return self.sep.join(self.cols)

class csv_record:

    def __init__(self, info, line, vals):
        self.info = info
        self.line = line
        self.vals = vals

    def index(self, col):
        if col in self.info.cols:
            return self.info.cols.index(col)
        elif type(col) == int and col < len(self.vals):
            return col

        return -1

    def get(self, col):
        _idx = self.index(col)

        if _idx < 0:
            return None

        return self.vals[_idx]

    def getfloat(self, col):
        _v = self.get(col)
        if _v == None:
            return None
        return float(_v)

    def getint(self, col):
        _v = self.get(col)
        if _v == None:
            return None
        return int(_v)

    def set(self, col, val, style='%s'):
        _idx = self.index(col)

        if _idx < 0:
            raise Exception('column not found %s' % col)

        self.vals[_idx] = style % val

    def __str__(self):
        return self.info.sep.join(self.vals)

def _format_value(n):
    _n = n.strip()

    if len(_n) > 1:
        if _n[0] in ['"', '\'']:
            _n = _n[1:]

    if len(_n) > 1:
        if _n[-1] in ['"', '\'']:
            _n = _n[:-1]

    return _n

def open(f, sep=',', skip_error=False):
    import logging
    import builtins 

    _cls = None

    with builtins.open(f) as _fi:
        _line = -1
        for _l in _fi.read().strip().splitlines():
            _l = _l.strip()
            if not _l:
                # skip empty lines
                continue

            _vs = list(map(_format_value, _l.split(sep)))

            if _cls == None:
                _cls = csv_class(f, _vs, sep)
            else:
                _line += 1

                if len(_vs) != len(_cls.cols):
                    _t = 'number of values (%s) does not match with the number of columns (%s) (%s)' % \
                            (len(_vs), len(_cls.cols), _l)

                    logging.error(_t)
                    if not skip_error:
                        raise Exception(_t)
                    continue

                yield csv_record(_cls, _line, _vs)

def parse_val(t, v):
    if t == 'int':
        return int(v)

    if t == 'float':
        return float(v)

    return v

