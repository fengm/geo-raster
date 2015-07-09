import numpy as np
cimport numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)

def stat(bnd):
	cdef np.ndarray[np.uint8_t, ndim=2] _dat = bnd.data
	cdef int _rows = bnd.height, _cols = bnd.width, _col, _row, _val

	import collections
	_stat = collections.defaultdict(lambda: 0.0)

	for _row in xrange(_rows):
		for _col in xrange(_cols):
			_val = _dat[_row, _col]
			_stat[_val] += 1
	
	return _stat

