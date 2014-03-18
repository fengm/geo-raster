
import numpy as np
cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def combine(np.ndarray[np.uint8_t, ndim=2] dat1, int nodata1, np.ndarray[np.uint8_t, ndim=2] dat2, int nodata2):
	cdef int _row, _col
	cdef int _rows = dat1.shape[0], _cols = dat1.shape[1]
	cdef int _v1, _v2
	cdef float _num = 0.0

	for _row in xrange(_rows):
		for _col in xrange(_cols):
			_v1 = dat1[_row, _col]
			_v2 = dat2[_row, _col]

			if _v1 != nodata1:
				continue

			if _v2 == nodata2:
				continue

			dat1[_row, _col] = _v2
			_num += 1.0

	return _num

