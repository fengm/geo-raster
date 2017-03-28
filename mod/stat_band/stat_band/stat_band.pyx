import numpy as np
cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def stat(bnd):
	import geo_raster as ge

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

	import collections
	_stat = collections.defaultdict(lambda: 0.0)

	for _row in xrange(_rows):
		for _col in xrange(_cols):
			_val = _dat[_row, _col]
			_stat[_val] += 1

	return _stat

def stat_int16(bnd):
	cdef np.ndarray[np.int16_t, ndim=2] _dat = bnd.data
	cdef int _rows = bnd.height, _cols = bnd.width, _col, _row, _val

	import collections
	_stat = collections.defaultdict(lambda: 0.0)

	for _row in xrange(_rows):
		for _col in xrange(_cols):
			_val = _dat[_row, _col]
			_stat[_val] += 1

	return _stat

def stat_uint16(bnd):
	cdef np.ndarray[np.uint16_t, ndim=2] _dat = bnd.data
	cdef int _rows = bnd.height, _cols = bnd.width, _col, _row, _val

	import collections
	_stat = collections.defaultdict(lambda: 0.0)

	for _row in xrange(_rows):
		for _col in xrange(_cols):
			_val = _dat[_row, _col]
			_stat[_val] += 1

	return _stat

