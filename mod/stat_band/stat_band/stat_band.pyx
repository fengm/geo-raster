import numpy as np
cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def stat(bnd):
    from . import geo_raster as ge

    if bnd.pixel_type == ge.pixel_type():
        return stat_uint8(bnd)

    if bnd.pixel_type == ge.pixel_type('short'):
        return stat_int16(bnd)

    if bnd.pixel_type == ge.pixel_type('ushort'):
        return stat_uint16(bnd)

    raise Exception('does not support the band type %s' % bnd.pixel_type)

def stat_uint8(bnd):
    cdef np.ndarray[np.uint8_t, ndim=2] _dat = bnd.data
    cdef int _rows = bnd.height, _cols = bnd.width, _col, _row, _val

    _stat = {}
    for _row in xrange(_rows):
        for _col in xrange(_cols):
            _val = _dat[_row, _col]
            _stat[_val] = _stat.get(_val, 0.0) + 1

    return _stat

def stat_int16(bnd):
    cdef np.ndarray[np.int16_t, ndim=2] _dat = bnd.data
    cdef int _rows = bnd.height, _cols = bnd.width, _col, _row, _val

    _stat = {}

    for _row in xrange(_rows):
        for _col in xrange(_cols):
            _val = _dat[_row, _col]
            _stat[_val] = _stat.get(_val, 0.0) + 1

    return _stat

def stat_uint16(bnd):
    cdef np.ndarray[np.uint16_t, ndim=2] _dat = bnd.data
    cdef int _rows = bnd.height, _cols = bnd.width, _col, _row, _val

    _stat = {}

    for _row in xrange(_rows):
        for _col in xrange(_cols):
            _val = _dat[_row, _col]
            _stat[_val] = _stat.get(_val, 0.0) + 1

    return _stat

def get_lat(x, y, proj_s, proj_t):
    from . import geo_base as gb
    
    _pt = gb.geo_point(x, y, proj_s)
    return _pt.project_to(proj_t).y
    
def sum_change_lats(bnd, stat):
    '''a temporary function for calculating the distribution of the latitudes for changes in each year'''
    cdef np.ndarray[np.uint8_t, ndim=2] _dat = bnd.data
    
    cdef int _row, _col, _v
    cdef float _x, _y
    
    _num = (_dat <= 100).sum()
    if _num <= 0:
        return False

    from . import geo_base as gb
    _proj_geo = gb.proj_from_epsg()
    
    for _row in range(bnd.height):
        _x, _y = bnd.to_location(bnd.width // 2, _row)
        _lat = round(get_lat(_x, _y, bnd.proj, _proj_geo), 4)

        for _col in range(bnd.width):
            _v = _dat[_row, _col]
            if _v > 50:
                continue

            _year = _v + 1970
            if _year not in stat:
                stat[_year] = {}
                
            stat[_year][_lat] = stat[_year].get(_lat, 0.0) + 1.0
    
    return True
