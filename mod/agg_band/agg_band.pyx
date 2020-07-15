'''
File: aggregate_band.py
Author: Min Feng
Version: 0.1
Create: 2013-04-21 02:03:33
Description: Aggregate band to match another band
'''
'''
Version: 0.2
Date: 2013-10-17 19:52:25
Note: add the function for calculating STD for each averaged pixel
'''

import numpy as np
import math
import logging
import collections

cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def mean(bnd_in, bnd_ot, float v_min=0, float v_max=100):
    if bnd_in is None:
        return None
    if bnd_ot is None:
        return None

    _geo_in = list(bnd_in.geo_transform)
    _geo_ot = list(bnd_ot.geo_transform)

    cdef float _cell_in = _geo_in[1]
    cdef float _cell_ot = _geo_ot[1]

    cdef float _dive = _cell_ot / _cell_in
    _size = [bnd_ot.height, bnd_ot.width]
    _offs = [(_geo_ot[3] - _geo_in[3]) / _geo_in[5],
                (_geo_ot[0] - _geo_in[0]) / _geo_in[1]]

    _nodata = bnd_in.get_nodata()
    _dat = bnd_in.data

    if bnd_in.data.dtype != np.float32:
        _dat = _dat.astype(np.float32)

    _dat = average_pixels(_dat,
            _offs[0], _offs[1], _dive,
            _nodata, _size[0], _size[1], v_min, v_max)

    if bnd_in.data.dtype != np.float32:
        _dat = _dat.astype(bnd_in.data.dtype)

    from . import geo_raster as ge
    return ge.geo_band_cache(_dat, _geo_ot, bnd_ot.proj,
                _nodata, bnd_in.pixel_type)

def median(bnd_in, bnd_ot, pro_nodata, zero_rate=1.0):
    if bnd_in is None:
        return None
    if bnd_ot is None:
        return None

    _geo_in = list(bnd_in.geo_transform)
    _geo_ot = list(bnd_ot.geo_transform)

    cdef float _cell_in = _geo_in[1]
    cdef float _cell_ot = _geo_ot[1]

    cdef float _dive = _cell_ot / _cell_in
    _size = [bnd_ot.height, bnd_ot.width]
    _offs = [(_geo_ot[3] - _geo_in[3]) / _geo_in[5],
                (_geo_ot[0] - _geo_in[0]) / _geo_in[1]]

    _nodata = bnd_in.get_nodata()
    _dat = bnd_in.data

    if bnd_in.data.dtype != np.int16:
        _dat = _dat.astype(np.int16)

    _dat = median_pixels(_dat,
            _offs[0], _offs[1], _dive,
            _nodata, _size[0], _size[1], pro_nodata, zero_rate=zero_rate)

    if bnd_in.data.dtype != np.int16:
        _dat = _dat.astype(bnd_in.data.dtype)

    from . import geo_raster as ge
    return ge.geo_band_cache(_dat, _geo_ot, bnd_ot.proj,
                _nodata, bnd_in.pixel_type)

def mean_std(bnd_in, bnd_ot):
    # only support float32 data type
    # assert(bnd_in.data.dtype == np.float32)

    _geo_in = list(bnd_in.geo_transform)
    _geo_ot = list(bnd_ot.geo_transform)

    cdef float _cell_in = _geo_in[1]
    cdef float _cell_ot = _geo_ot[1]

    cdef float _dive = _cell_ot / _cell_in
    _size = [bnd_ot.height, bnd_ot.width]
    _offs = [(_geo_ot[3] - _geo_in[3]) / _geo_in[5],
                (_geo_ot[0] - _geo_in[0]) / _geo_in[1]]

    _nodata = bnd_in.get_nodata()
    _dat = bnd_in.data

    if bnd_in.data.dtype != np.float32:
        _dat = _dat.astype(np.float32)

    _dat = average_std(_dat,
            _offs[0], _offs[1], _dive,
            bnd_in.get_nodata(), _size[0], _size[1])

    if bnd_in.data.dtype != np.float32:
        _dat = _dat.astype(bnd_in.data.dtype)

    from . import geo_raster as ge
    return ge.geo_band_cache(_dat, _geo_ot, bnd_ot.proj,
                _nodata, ge.pixel_type('float'))

def average_pixels(np.ndarray[np.float32_t, ndim=2] dat,
        float off_y, float off_x, float scale,
        float nodata, unsigned int rows, unsigned int cols, float v_min, float v_max):

    cdef unsigned int _rows_o, _cols_o
    cdef unsigned int _rows_n, _cols_n

    _rows_o = dat.shape[0]
    _cols_o = dat.shape[1]

    # _rows_n = int(math.ceil(_rows_o / scale))
    # _cols_n = int(math.ceil(_cols_o / scale))

    _rows_n = rows
    _cols_n = cols

    cdef unsigned int _row_o, _col_o
    cdef unsigned int _row_n, _col_n

    cdef int _row_min, _row_max
    cdef int _col_min, _col_max

    cdef float _row_min_f, _row_max_f
    cdef float _col_min_f, _col_max_f

    cdef double _vs
    cdef double _ns
    cdef float _a

    cdef float _nodata
    _nodata = nodata

    _dat = np.empty([_rows_n, _cols_n], np.float32)
    _dat.fill(_nodata)

    _row_min_f = off_y - scale
    for _row_n from 0<=_row_n<_rows_n:
        _row_min_f = _row_min_f + scale
        _row_max_f = _row_min_f + scale

        _col_min_f = off_x - scale
        for _col_n from 0<=_col_n<_cols_n:
            _col_min_f = _col_min_f + scale
            _col_max_f = _col_min_f + scale

            if _row_max_f <= 0 or _col_max_f <= 0 or \
                    _row_min_f >= _rows_o or _col_min_f >= _cols_o:
                continue

            _row_min = int(math.floor(_row_min_f))
            _row_min = max(0, _row_min)

            _col_min = int(math.floor(_col_min_f))
            _col_min = max(0, _col_min)

            _row_max = int(math.ceil(_row_max_f))
            _row_max = min(_rows_o, _row_max)

            _col_max = int(math.ceil(_col_max_f))
            _col_max = min(_cols_o, _col_max)

            _vs = 0.0
            _ns = 0.0
            _aa = 0.0

            _ss = collections.defaultdict(lambda: 0.0)
            for _row_o from _row_min<=_row_o<_row_max:
                for _col_o from _col_min<=_col_o<_col_max:
                    _a = (min(_row_o + 1, _row_max_f) - \
                            max(_row_o, _row_min_f)) * \
                            (min(_col_o + 1, _col_max_f) - \
                            (max(_col_o, _col_min_f)))
                    _aa += _a

                    _v = dat[_row_o, _col_o]
                    if _v == _nodata or _v < v_min or _v > v_max:
                        _ss[_v] += _a
                        continue

                    _vs += _v * _a
                    _ns += _a

            if _aa <= 0.0:
                continue

            if _ns < _aa / 2:
                _vv = nodata
                _vx = 0 
                for _k, _v in _ss.items():
                    if _v > _vx:
                        _vv = _k
                        _vx = _v

                _dat[_row_n, _col_n] = _vv
                continue

            _dat[_row_n, _col_n] = _vs / _ns

    return _dat

cdef np.ndarray[np.float32_t, ndim=2] average_std(np.ndarray[np.float32_t, ndim=2] dat,
        float off_y, float off_x, float scale,
        float nodata, unsigned int rows, unsigned int cols):
    '''calculate the STD for each aggregated pixel'''

    cdef unsigned int _rows_o, _cols_o
    cdef unsigned int _rows_n, _cols_n

    _rows_o = dat.shape[0]
    _cols_o = dat.shape[1]

    _rows_n = rows
    _cols_n = cols

    cdef unsigned int _row_o, _col_o
    cdef unsigned int _row_n, _col_n

    cdef int _row_min, _row_max
    cdef int _col_min, _col_max

    cdef float _row_min_f, _row_max_f
    cdef float _col_min_f, _col_max_f

    cdef float _nodata
    _nodata = nodata

    _dat = np.empty([_rows_n, _cols_n], np.float32)
    _dat.fill(_nodata)

    _row_min_f = off_y - scale
    for _row_n from 0<=_row_n<_rows_n:
        _row_min_f = _row_min_f + scale
        _row_max_f = _row_min_f + scale

        _col_min_f = off_x - scale
        for _col_n from 0<=_col_n<_cols_n:
            _col_min_f = _col_min_f + scale
            _col_max_f = _col_min_f + scale

            if _row_max_f <= 0 or _col_max_f <= 0 or \
                    _row_min_f >= _rows_o or _col_min_f >= _cols_o:
                continue

            _row_min = int(math.floor(_row_min_f))
            _row_min = max(0, _row_min)

            _col_min = int(math.floor(_col_min_f))
            _col_min = max(0, _col_min)

            _row_max = int(math.ceil(_row_max_f))
            _row_max = min(_rows_o, _row_max)

            _col_max = int(math.ceil(_col_max_f))
            _col_max = min(_cols_o, _col_max)

            _vs = []
            for _row_o from _row_min<=_row_o<_row_max:
                for _col_o from _col_min<=_col_o<_col_max:
                    _v = dat[_row_o, _col_o]
                    if _v == _nodata:
                        continue
                    _vs.append(_v)

            if len(_vs) <= 0:
                continue

            _dat[_row_n, _col_n] = np.std(_vs)

    return _dat

def dominated(bnd_in, bnd_ot, weights=None):
    if bnd_in is None:
        return None
    if bnd_ot is None:
        return None

    _geo_in = list(bnd_in.geo_transform)
    _geo_ot = list(bnd_ot.geo_transform)

    cdef float _cell_in = _geo_in[1]
    cdef float _cell_ot = _geo_ot[1]

    cdef float _dive = _cell_ot / _cell_in
    _size = [bnd_ot.height, bnd_ot.width]
    _offs = [(_geo_ot[3] - _geo_in[3]) / _geo_in[5],
                (_geo_ot[0] - _geo_in[0]) / _geo_in[1]]

    _nodata = bnd_in.get_nodata()
    _dat = bnd_in.data

    if bnd_in.data.dtype != np.int16:
        _dat = _dat.astype(np.int16)

    _dat = dominated_pixels(_dat,
            _offs[0], _offs[1], _dive,
            _nodata, _size[0], _size[1], weights)

    if bnd_in.data.dtype != np.int16:
        _dat = _dat.astype(bnd_in.data.dtype)

    from . import geo_raster as ge
    return ge.geo_band_cache(_dat, _geo_ot, bnd_ot.proj,
                _nodata, bnd_in.pixel_type)

cdef np.ndarray[np.int16_t, ndim=2] dominated_pixels(np.ndarray[np.int16_t, ndim=2] dat,
        float off_y, float off_x, float scale,
        int nodata, unsigned int rows, unsigned int cols, weights):

    cdef unsigned int _rows_o, _cols_o
    cdef unsigned int _rows_n, _cols_n

    _rows_o = dat.shape[0]
    _cols_o = dat.shape[1]

    _rows_n = rows
    _cols_n = cols

    cdef unsigned int _row_o, _col_o
    cdef unsigned int _row_n, _col_n

    cdef int _row_min, _row_max
    cdef int _col_min, _col_max

    cdef float _row_min_f, _row_max_f
    cdef float _col_min_f, _col_max_f

    cdef double _ns, _as
    cdef float _a
    cdef int _tp, _vv

    cdef int _nodata
    _nodata = nodata

    _dat = np.empty([_rows_n, _cols_n], np.int16)
    _dat.fill(_nodata)

    _row_min_f = off_y - scale
    for _row_n from 0<=_row_n<_rows_n:
        _row_min_f = _row_min_f + scale
        _row_max_f = _row_min_f + scale

        _col_min_f = off_x - scale
        for _col_n from 0<=_col_n<_cols_n:
            _col_min_f = _col_min_f + scale
            _col_max_f = _col_min_f + scale

            if _row_max_f <= 0 or _col_max_f <= 0 or \
                    _row_min_f >= _rows_o or _col_min_f >= _cols_o:
                continue

            _row_min = int(math.floor(_row_min_f))
            _row_min = max(0, _row_min)

            _col_min = int(math.floor(_col_min_f))
            _col_min = max(0, _col_min)

            _row_max = int(math.ceil(_row_max_f))
            _row_max = min(_rows_o, _row_max)

            _col_max = int(math.ceil(_col_max_f))
            _col_max = min(_cols_o, _col_max)

            _vs = {}
            _ns = 0.0
            _as = 0.0
            _tp = False

            for _row_o from _row_min<=_row_o<_row_max:
                for _col_o from _col_min<=_col_o<_col_max:
                    _a = (min(_row_o + 1, _row_max_f) - \
                            max(_row_o, _row_min_f)) * \
                            (min(_col_o + 1, _col_max_f) - \
                            (max(_col_o, _col_min_f)))

                    if _a < 0.5:
                        continue

                    _as += _a

                    _v = dat[_row_o, _col_o]
                    # if _v == _nodata:
                    #     if pro_nodata:
                    #         _tp = True
                    #         break
                    #     else:
                    #         continue

                    _ns += _a
                    _vs[_v] = _vs.get(_v, 0) + 1

                if _tp:
                    break

            if _ns <= 0 or _tp:
                continue
            
            # if len(_vs.keys()) == 1:
            #     _dat[_row_n, _col_n] = list(_vs.values())[0]
            #     continue

            if weights is not None and len(weights) > 0:
                for _w_min, _w_max, _w_wet in weights:
                    for _kk in _vs:
                        if _w_min <= _kk <= _w_max:
                            _vs[_kk] *= _w_wet

            _mx = 0
            _vv == _nodata
            for _kk in _vs:
                if _vs[_kk] > _mx:
                    _mx = _vs[_kk]
                    _vv = _kk

            _dat[_row_n, _col_n] = _vv

    return _dat

cdef np.ndarray[np.int16_t, ndim=2] median_pixels(np.ndarray[np.int16_t, ndim=2] dat,
        float off_y, float off_x, float scale,
        int nodata, unsigned int rows, unsigned int cols, pro_nodata, zero_rate):

    cdef unsigned int _rows_o, _cols_o
    cdef unsigned int _rows_n, _cols_n

    _rows_o = dat.shape[0]
    _cols_o = dat.shape[1]

    _rows_n = rows
    _cols_n = cols

    cdef unsigned int _row_o, _col_o
    cdef unsigned int _row_n, _col_n

    cdef int _row_min, _row_max
    cdef int _col_min, _col_max

    cdef float _row_min_f, _row_max_f
    cdef float _col_min_f, _col_max_f

    cdef double _ns
    cdef float _a
    cdef int _tp, _vv

    cdef int _nodata
    _nodata = nodata

    import random

    _dat = np.empty([_rows_n, _cols_n], np.int16)
    _dat.fill(_nodata)

    _row_min_f = off_y - scale
    for _row_n from 0<=_row_n<_rows_n:
        _row_min_f = _row_min_f + scale
        _row_max_f = _row_min_f + scale

        _col_min_f = off_x - scale
        for _col_n from 0<=_col_n<_cols_n:
            _col_min_f = _col_min_f + scale
            _col_max_f = _col_min_f + scale

            if _row_max_f <= 0 or _col_max_f <= 0 or \
                    _row_min_f >= _rows_o or _col_min_f >= _cols_o:
                continue

            _row_min = int(math.floor(_row_min_f))
            _row_min = max(0, _row_min)

            _col_min = int(math.floor(_col_min_f))
            _col_min = max(0, _col_min)

            _row_max = int(math.ceil(_row_max_f))
            _row_max = min(_rows_o, _row_max)

            _col_max = int(math.ceil(_col_max_f))
            _col_max = min(_cols_o, _col_max)

            _vs = []
            _ns = 0
            _tp = False

            for _row_o from _row_min<=_row_o<_row_max:
                for _col_o from _col_min<=_col_o<_col_max:
                    _a = (min(_row_o + 1, _row_max_f) - \
                            max(_row_o, _row_min_f)) * \
                            (min(_col_o + 1, _col_max_f) - \
                            (max(_col_o, _col_min_f)))

                    if _a < 0.5:
                        continue

                    _v = dat[_row_o, _col_o]
                    if _v == _nodata:
                        if pro_nodata:
                            _tp = True
                            break
                        else:
                            continue

                    if _v == 0:
                        if zero_rate <= 0:
                            continue

                        if len(_vs) > 0:
                            if zero_rate < 1.0:
                                if random.random() > zero_rate:
                                    continue

                    _ns += _a
                    _vs.append(_v)

                if _tp:
                    break

            if _ns <= 0 or _tp:
                continue

            _mx = 0
            _vv == _nodata

            _len = len(_vs)
            if _len > 0:
                if _len <= 2:
                    _vv = _vs[0]
                else:
                    _vs.sort()
                    _vv = _vs[int(_len / 2)]

            _dat[_row_n, _col_n] = _vv

    return _dat


def perc(bnd_in, bnd_ot, val, valid_values=None, excluded_values=None, nodata=255, \
            exclude_nodata=False, scale=100, pixel_type='byte'):
    '''aggregate the values to percentage of the pixels'''

    _geo_in = list(bnd_in.geo_transform)
    _geo_ot = list(bnd_ot.geo_transform)

    cdef float _cell_in = _geo_in[1]
    cdef float _cell_ot = _geo_ot[1]

    cdef float _dive = _cell_ot / _cell_in
    _size = [bnd_ot.height, bnd_ot.width]
    _offs = [(_geo_ot[3] - _geo_in[3]) / _geo_in[5],
                (_geo_ot[0] - _geo_in[0]) / _geo_in[1]]

    _dat = bnd_in.data

    if bnd_in.data.dtype != np.uint8:
        _dat = _dat.astype(np.uint8)

    _dat = perc_pixels(_dat,
            _offs[0], _offs[1], _dive, val, valid_values, excluded_values,
            bnd_in.nodata, nodata, _size[0], _size[1], 1 if exclude_nodata else 0, int(scale))

    from . import geo_raster as ge
    from . import geo_base as gb

    _pt = ge.pixel_type(pixel_type)
    return ge.geo_band_cache(_dat.astype(gb.to_dtype(_pt)), _geo_ot, bnd_ot.proj, 
                nodata, _pt)

cdef np.ndarray[np.float32_t, ndim=2] perc_pixels(np.ndarray[np.uint8_t, ndim=2] dat,
        float off_y, float off_x, float scale, int val, valid_values, excluded_values,
        int s_nodata, int t_nodata, unsigned int rows, unsigned int cols, int exclude_nodata, int scale_val):

    cdef unsigned int _rows_o, _cols_o
    cdef unsigned int _rows_n, _cols_n

    _rows_o = dat.shape[0]
    _cols_o = dat.shape[1]

    _rows_n = rows
    _cols_n = cols

    cdef unsigned int _row_o, _col_o
    cdef unsigned int _row_n, _col_n

    cdef int _row_min, _row_max
    cdef int _col_min, _col_max

    cdef float _row_min_f, _row_max_f
    cdef float _col_min_f, _col_max_f

    cdef double _vs
    cdef double _ns
    cdef double _as
    cdef float _a

    cdef int _v
    cdef float _vv

    _dat = np.empty([_rows_n, _cols_n], np.float32)
    logging.debug('aggregating nodata: %s, %s' % (s_nodata, t_nodata))
    _dat.fill(t_nodata)

    _row_min_f = off_y - scale
    for _row_n from 0<=_row_n<_rows_n:
        _row_min_f = _row_min_f + scale
        _row_max_f = _row_min_f + scale

        _col_min_f = off_x - scale
        for _col_n from 0<=_col_n<_cols_n:
            _col_min_f = _col_min_f + scale
            _col_max_f = _col_min_f + scale

            if _row_max_f <= 0 or _col_max_f <= 0 or \
                    _row_min_f >= _rows_o or _col_min_f >= _cols_o:
                continue

            _row_min = int(math.floor(_row_min_f))
            _row_min = max(0, _row_min)

            _col_min = int(math.floor(_col_min_f))
            _col_min = max(0, _col_min)

            _row_max = int(math.ceil(_row_max_f))
            _row_max = min(_rows_o, _row_max)

            _col_max = int(math.ceil(_col_max_f))
            _col_max = min(_cols_o, _col_max)

            _vs = 0.0
            _ns = 0.0
            _as = 0.0
            for _row_o from _row_min<=_row_o<_row_max:
                for _col_o from _col_min<=_col_o<_col_max:
                    _a = (min(_row_o + 1, _row_max_f) - \
                            max(_row_o, _row_min_f)) * \
                            (min(_col_o + 1, _col_max_f) - \
                            (max(_col_o, _col_min_f)))

                    _as += _a

                    _v = dat[_row_o, _col_o]
                    if _v is None:
                        continue

                    # if exclude_nodata == 1 and (_v > 10 or _v == s_nodata):
                    # if _v > 10 or _v == s_nodata:
                    if _v == s_nodata:
                        continue

                    if valid_values is not None and len(valid_values) > 0:
                        if _v not in valid_values:
                            continue

                    if excluded_values is not None and len(excluded_values) > 0:
                        if _v in excluded_values:
                            continue

                    _z = 1 if (_v == val) else 0

                    _vs += _z * _a
                    _ns += _a

            if _ns <= 0.0:
                continue

            if _ns < 0.5 * _as:
                continue

            if _vs == 0:
                _dat[_row_n, _col_n] = 0
                continue

            _vv = (float(scale_val) * _vs) / _ns

            if _vv > scale_val:
                _vv = scale_val
            if _vv < 0:
                _vv = 0

            _dat[_row_n, _col_n] = _vv

    return _dat

