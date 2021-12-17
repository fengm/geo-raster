'''
File: geo_interpolate.pyx
Author: Min Feng
Version: 0.1
Create: 2013-05-14 14:46:51
Description: classes for interpolation with geospatial raster or points
'''

import numpy as np
import logging

cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def band_idw(bnd, bnd_tar, int dist, float power, float nodata=-9999):
	# the interpolate method only support float data type
	assert bnd.data.dtype == np.float32

	cdef np.ndarray[np.float32_t, ndim=2] _dat = np.empty((bnd_tar.height, bnd_tar.width), dtype=np.float32)
	_nodata = bnd.nodata if bnd.nodata != None else nodata
	_dat.fill(nodata)

	import geo_raster_ex as gx
	_proj = gx.projection_transform.from_band(bnd_tar, bnd.proj)

	import progress_percentage
	_ppp = progress_percentage.progress_percentage(bnd_tar.height)

	cdef int _row, _col
	for _row in xrange(bnd_tar.height):
		_ppp.next()
		for _col in xrange(bnd_tar.width):
			_x, _y = _proj.project(_col, _row)
			_v = band_idw_loc(bnd, _x, _y, dist, power)
			if _v != None:
				_dat[_row, _col] = _v

	_ppp.done()

	import geo_raster as ge
	_bnd = ge.geo_band_cache(_dat, bnd_tar.geo_transform, bnd_tar.proj, _nodata, ge.pixel_type('float'))
	return _bnd

def band_idw_loc(bnd, float x, float y, float dist, float power) :
	cdef np.ndarray[np.float32_t, ndim=2] _dat = bnd.data
	cdef int _col0, _row0
	cdef float _x1, _y1
	cdef int _rows = _dat.shape[0], _cols = _dat.shape[1]

	# check if the point is within the raster extent
	_col0, _row0 = bnd.to_cell(x, y)
	if _col0 < 0 or _row0 < 0 or _col0 >= _cols or _row0 >= _rows:
		logging.warning('out of raster extent: %s, %s' % (x, y))
		return None

	_x1, _y1 = bnd.to_location(_col0, _row0)
	if x == _x1 and y == _y1:
		return _dat[_row0, _col0]

	import math
	cdef int _dist = int(math.ceil(dist))

	_xrange = range(max(0, _col0 - _dist), min(_cols, _col0 + _dist + 1))
	_yrange = range(max(0, _row0 - _dist), min(_rows, _row0 + _dist + 1))

	_loc = bnd.to_location(_xrange[0], _yrange[0])

	cdef float _vs = 0, _ds = 0
	cdef int _cs = 0, _r, _c
	cdef float _xs = _loc[0], _ys = _loc[1], _x, _y, _v

	_cell = bnd.geo_transform[1]
	cdef _max_d = _cell * dist

	_y = _ys + _cell
	for _r in _yrange:
		_y -= _cell
		_x = _xs - _cell

		for _c in _xrange:
			_x += _cell
			_v = _dat[_r, _c]
			if _v != None:
				_d = math.hypot(_x - x, _y - y)

				if _d <= 0:
					return _v

				if _d > _max_d:
					continue

				_d = 1.0 / (_d ** power)

				_vs += _v * _d
				_ds += _d
				_cs += 1

	if _ds == 0:
		return None

	return _vs / _ds

