'''
File: mod_filter.pyx
Author: Min Feng
Version: 0.1
Create: 2018-01-11 14:06:00
Description: filter out noises
'''

import collections
import numpy as np
import math
import logging

cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def filter_band_mmu(bnd, num=3, area=None):
    from skimage import morphology
    
    _num = num
    if area is not None:
        _area = area
        if bnd.proj.IsGeographic():
            _area = _area / (120000 ** 2)
        _num = max(_num, int(_area / (bnd.cell_size ** 2)))
    
    _dat = bnd.data
    _dat = morphology.area_closing(_dat, _num)
    _dat = morphology.area_opening(_dat, _num)
    
    bnd.data = _dat
        
def filter_band_median(bnd, s=1, it=1):
    from gio import mod_filter
    from gio import stat_band
    from gio import config
    import logging
    
    _ss = stat_band.stat(bnd)
    _vs = [_v for _v in _ss.keys()]

    if len(_vs) <= 1:
        return

    _nodata = bnd.nodata
    bnd.nodata = 300

    for _i in xrange(it):
        _num = mod_filter.median(bnd, s)
        logging.debug('filtered %s %s pixels' % (_i, _num))
        if _num < 100:
            break

    bnd.nodata = _nodata

def median(bnd, float dis, vs=None):
    cdef int _rows = bnd.height, _cols = bnd.width
    cdef int _row, _col, _v, _vo
    cdef int _nodata = bnd.nodata
    cdef np.ndarray[np.uint8_t, ndim=2] _dat = bnd.data
    cdef np.ndarray[np.uint8_t, ndim=2] _dat_rep = bnd.data.astype(np.uint8)
    cdef int _t = 0

    for _row in xrange(_rows):
        for _col in xrange(_cols):
            _vo = _dat[_row, _col]

            if _vo == _nodata:
                continue

            if vs is not None:
                if _v not in vs:
                    continue

            _v = _median(_dat, _col, _row, dis, _nodata, _dat_rep)
            if _v != _vo:
                _t += 1

    bnd.data = _dat_rep
    return _t

cdef _median(np.ndarray[np.uint8_t, ndim=2] dat, int col, int row, float dis, int nodata, \
        np.ndarray[np.uint8_t, ndim=2] rep):
    cdef int _row, _col
    cdef int _v, _vv

    _vv = dat[row, col]
    if _vv == nodata:
        return nodata

    cdef int _dis = int(dis)

    cdef int _row_s = max(0, row - _dis), _row_e = min(dat.shape[0], row + _dis + 1)
    cdef int _col_s = max(0, col - _dis), _col_e = min(dat.shape[1], col + _dis + 1)

    cdef int _num_wat = 0
    cdef int _num_non = 0

    _vs = []
    for _row in xrange(_row_s, _row_e):
        for _col in xrange(_col_s, _col_e):
            _v = dat[_row, _col]
            if _v == nodata:
                continue

            _vs.append(_v)

    if len(_vs) == 0:
        return nodata

    _v = sorted(_vs)[len(_vs) / 2]
    rep[row, col] = _v

    return _v

def clean(bnd, float dis, int min_num, vs=None):
    cdef int _rows = bnd.height, _cols = bnd.width
    cdef int _row, _col, _v, _vo
    cdef int _nodata = bnd.nodata
    cdef np.ndarray[np.uint8_t, ndim=2] _dat = bnd.data
    cdef np.ndarray[np.uint8_t, ndim=2] _dat_rep = bnd.data.astype(np.uint8)
    cdef int _t = 0

    for _row in xrange(_rows):
        for _col in xrange(_cols):
            _vo = _dat[_row, _col]

            if _vo == _nodata:
                continue

            if vs is not None:
                if _v not in vs:
                    continue

            _n1, _v1 = _stat(_dat, _col, _row, dis, min_num, _nodata)
            if _n1 == 0 or _n1 >= min_num:
                continue

            _n2, _v2 = _stat(_dat, _col, _row, dis + 1, min_num, _nodata)
            if _n2 > _n1:
                continue

            _dat_rep[_row, _col] = _v2
            _t += 1

    bnd.data = _dat_rep
    return _t

def init_zero():
    return 0

cdef stat_pixel(np.ndarray[np.uint8_t, ndim=2] dat, int col, int row, float dis, int min_num, int nodata):
    cdef int _row, _col
    cdef int _v, _vv

    _vv = dat[row, col]
    if _vv == nodata:
        return nodata

    cdef int _dis = int(dis)

    cdef int _row_s = max(0, row - _dis), _row_e = min(dat.shape[0], row + _dis + 1)
    cdef int _col_s = max(0, col - _dis), _col_e = min(dat.shape[1], col + _dis + 1)

    cdef int _num = 0

    _ss = collections.defaultdict(init_zero)
    for _row in xrange(_row_s, _row_e):
        for _col in xrange(_col_s, _col_e):
            _v = dat[_row, _col]
            if _v == nodata:
                continue

            _d = math.hypot(_row - row, _col - col)
            if _d > dis:
                continue

            if _v == _vv:
                _num += 1

                if _num >= min_num:
                    return _vv

            _ss[_v] += 1
    
    _v = max(_ss.values())
    for _k in _ss:
        if _ss[_k] == _v:
            return _k

    raise Exception('failed to find the dominated value')

cdef _stat(np.ndarray[np.uint8_t, ndim=2] dat, int col, int row, float dis, int min_num, int nodata):
    cdef int _row, _col
    cdef int _v, _vv

    _vv = dat[row, col]
    if _vv == nodata:
        return 0, nodata

    cdef int _dis = int(dis)

    cdef int _row_s = max(0, row - _dis), _row_e = min(dat.shape[0], row + _dis + 1)
    cdef int _col_s = max(0, col - _dis), _col_e = min(dat.shape[1], col + _dis + 1)

    cdef int _num_wat = 0
    cdef int _num_non = 0

    _vs = {}

    for _row in xrange(_row_s, _row_e):
        for _col in xrange(_col_s, _col_e):
            _d = math.hypot(_row, _col)
            if _d > dis:
                continue

            if _row == row and _col == col:
                continue

            _v = dat[_row, _col]
            if _v == nodata:
                continue

            if _v not in _vs:
                _vs[_v] = 0

            _vs[_v] += 1

            if _v == _vv and _vs[_v] >= min_num:
                return _vs[_v], _v

    if len(_vs.keys()) == 0:
        return 0, nodata

    _max_k = _vs.keys()[0]
    _max_v = _vs[_max_k]

    for _k, _v in _vs.items():
        if _v > _max_v:
            _max_k = _k
            _max_v = _v

    return _vs.get(_vv, 0), _max_k

def expand(np.ndarray[np.uint8_t, ndim=2] dat, np.ndarray[np.uint8_t, ndim=2, cast=True] ref, val, non, dist, min_num):
    from gio import config

    cdef int _rows = dat.shape[0], _cols = dat.shape[1]
    cdef int _row, _col, _vw, _vr

    cdef int _t = 0

    cdef int _dis = dist
    cdef int _min_num = min_num

    logging.info('expand dis: %s, min num: %s' % (_dis, _min_num))

    for _row in xrange(_rows):
        for _col in xrange(_cols):
            _vw = dat[_row, _col]
            _vr = ref[_row, _col]

            if _vw != non:
                continue

            if _vr == 1 and _near(dat, _col, _row, _dis, _min_num, val) == 1:
                dat[_row, _col] = 199
                _t += 1
    
    dat[dat == 199] = val
    return _t

cdef _near(np.ndarray[np.uint8_t, ndim=2] dat, int col, int row, float dis, int num, int val):
    cdef int _row, _col
    cdef int _v, _vv = dat[row, col]

    cdef int _dis = int(dis)

    cdef int _row_s = max(0, row - _dis), _row_e = min(dat.shape[0], row + _dis + 1)
    cdef int _col_s = max(0, col - _dis), _col_e = min(dat.shape[1], col + _dis + 1)

    cdef int _num = 0
    for _row in xrange(_row_s, _row_e):
        for _col in xrange(_col_s, _col_e):
            _v = dat[_row, _col]

            if _v != val:
                continue

            # _d = math.hypot(_row - row, _col - col)
            # if _d > dis:
            #     continue

            _num += 1
            if _num >= num:
                return 1

    return 0

