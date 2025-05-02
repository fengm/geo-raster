'''
File: filter_band.pyx
Author: Min Feng
Version: 0.1
Create: 2015-09-18 15:58:24
Description: 
'''

import numpy as np
import collections

cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def mmu(bnd, float dis, int min_num):
	cdef int _rows = bnd.height, _cols = bnd.width
	cdef int _row, _col, _v, _vo
	cdef int _nodata = bnd.nodata
	cdef np.ndarray[np.uint8_t, ndim=2] _dat = bnd.data
	cdef np.ndarray[np.uint8_t, ndim=2] _ddd = _dat.clone()
	cdef int _t = 0

	for _row in xrange(_rows):
		for _col in xrange(_cols):
			_vo = _dat[_row, _col]

			if _vo == _nodata:
				continue

			_ddd[_row, _col] = _stat(_dat, _col, _row, dis, min_num, _nodata, _vo)
	
	return bnd.from_grid(_ddd, nodata=_nodata)

def _stat(np.ndarray[np.uint8_t, ndim=2] dat, int col, int row, float dis, int min_num, int nodata, int val):
	cdef int _row, _col
	cdef int _v, _vv

	cdef int _dis = int(dis)

	cdef int _row_s = max(0, row - _dis), _row_e = min(dat.shape[0], row + _dis + 1)
	cdef int _col_s = max(0, col - _dis), _col_e = min(dat.shape[1], col + _dis + 1)

	cdef int _num_wat = 0
	cdef int _num_non = 0

	_vs = collections.defaultdict(lambda: 0)
	_vn = 0

	for _row in xrange(_row_s, _row_e):
		for _col in xrange(_col_s, _col_e):
			if _row == row and _col == col:
				# skip the pixel itself
				continue

			_v = dat[_row, _col]
			if _v == nodata:
				continue

			if _v == val:
				_vn += 1
				if _vn >= min_num:
					return val
				continue
			
			_vs[_v] += _vs.get(_v, 0) + 1
	
	_max_val = max(_vs.values())
	for _k, _v in _vs.items():
		if _v == _max_val:
			return _k

	return nodata

