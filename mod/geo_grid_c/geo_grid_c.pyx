'''
File: geo_grid_c.pyx
Author: Min Feng
Version: 0.1
Create: 2016-01-25 10:43:56
Description: provide utilities for grid operations
'''
import numpy as np
cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

class neighbor:

	def vary(self, np.ndarray[np.uint8_t, ndim=2] dat, dist):
		cdef int _rows = dat.shape[0], _cols = dat.shape[1]
		cdef int _rrr, _ccc
		cdef int _row, _col, _v
		cdef np.ndarray[np.uint8_t, ndim=2] _var = np.zeros((_rows, _cols), dtype=np.uint8)

		for _row in xrange(_rows):
			for _col in xrange(_cols):
				_vs = []
				for _rrr in xrange(max(0, _row - dist), min(_rows, _row + dist)):
					for _ccc in xrange(max(0, _col - dist), min(_cols, _col + dist)):
						_v = dat[_rrr, _ccc]
						if _v not in _vs:
							_vs.append(_v)

				_var[_row, _col] = len(_vs)

		return _var

	def range(self, np.ndarray[np.float32_t, ndim=2] dat, dist):
		cdef int _rows = dat.shape[0], _cols = dat.shape[1]
		cdef int _rrr, _ccc
		cdef int _row, _col
		cdef float _v

		cdef np.ndarray[np.float32_t, ndim=2] _var = np.zeros((_rows, _cols), dtype=np.float32)

		for _row in xrange(_rows):
			for _col in xrange(_cols):
				_vs = []
				for _rrr in xrange(max(0, _row - dist), min(_rows, _row + dist)):
					for _ccc in xrange(max(0, _col - dist), min(_cols, _col + dist)):
						_v = dat[_rrr, _ccc]
						if _v not in _vs:
							_vs.append(_v)

				_var[_row, _col] = max(_vs) - min(_vs)

		return _var

