

import numpy as np
cimport numpy as np
cimport cython
import math

@cython.boundscheck(False)

def average_pixels_byte(np.ndarray[np.uint8_t, ndim=2] dat, 
		float off_y, float off_x, float scale, 
		int nodata, unsigned int rows, unsigned int cols):

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

	cdef int _nodata
	_nodata = nodata

	_dat = np.empty([_rows_n, _cols_n], np.uint8)
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

			_vs = 0
			_ns = 0
			for _row_o from _row_min<=_row_o<_row_max:
				for _col_o from _col_min<=_col_o<_col_max:
					_a = (min(_row_o + 1, _row_max_f) - \
							max(_row_o, _row_min_f)) * \
							(min(_col_o + 1, _col_max_f) - \
							(max(_col_o, _col_min_f)))

					_v = dat[_row_o, _col_o]
					if _v == _nodata:
						continue

					_vs += _v * _a
					_ns += _a

			if _ns <= 0:
				continue

			_dat[_row_n, _col_n] = int(_vs / _ns)
	
	return _dat

def average_pixels_int16(np.ndarray[np.int16_t, ndim=2] dat, 
		float off_y, float off_x, float scale, 
		int nodata, unsigned int rows, unsigned int cols):

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
	cdef int _vv, _vr

	cdef int _nodata
	_nodata = nodata

	_dat = np.empty([_rows_n, _cols_n], np.int16)
	_dat.fill(_nodata)

	_dat_r = np.empty([_rows_n, _cols_n], np.uint8)
	_dat_r.fill(255)

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

			_vs = 0
			_ns = 0
			for _row_o from _row_min<=_row_o<_row_max:
				for _col_o from _col_min<=_col_o<_col_max:
					_a = (min(_row_o + 1, _row_max_f) - \
							max(_row_o, _row_min_f)) * \
							(min(_col_o + 1, _col_max_f) - \
							(max(_col_o, _col_min_f)))

					_v = dat[_row_o, _col_o]
					if _v == _nodata:
						continue

					_vs += _v * _a
					_ns += _a

			if _ns <= 0:
				continue

			_vv = int(_vs / _ns)
			_dat[_row_n, _col_n] = _vv 

			if _vv == 0:
				_vr = 0
			else:
				_vr = int(100 * dat[_row_min:_row_max, \
						_col_min:_col_max].std() / abs(_vv))
				_vr = max(0, min(250, _vr))

			_dat_r[_row_n, _col_n] = _vr
	
	return _dat, _dat_r

def convert_qa(np.ndarray[np.int16_t, ndim=2] dat):
	'''
	covert the LEDAPS QA to a simpler QA
	0: valid
	1: water
	2: cloud
	3: snow
	9: unvalid
	'''

	cdef unsigned int _rows, _cols

	_rows = dat.shape[0]
	_cols = dat.shape[1]

	cdef int _row, _col
	cdef unsigned int _v, _vv
	
	_dat = np.empty([_rows, _cols], np.uint8)
	_dat.fill(0)

	for _row from 0<=_row<_rows:
		for _col from 0<=_col<_cols:
			_v = dat[_row, _col]

			_vv = 0
			if _v & 0x1 > 0:
				# unvalid pixel
				_vv = 9
			elif _v & 0x410 > 0:
				# snow pixel
				_vv = 3
			elif _v & 0x2300 > 0:
				# cloud pixel
				_vv = 2
			elif _v & 0x800 == 0:
				# water pixel
				_vv = 1
			else:
				continue

			_dat[_row, _col] = _vv
	
	return _dat

def average_pixels_max_occur(np.ndarray[np.uint8_t, ndim=2] dat, 
		float off_y, float off_x, float scale, 
		unsigned int nodata, 
		unsigned int rows, unsigned int cols):

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

	cdef int _cc, _vv
	cdef int _cm, _vm, _ct

	_dat = np.empty([_rows_n, _cols_n], np.uint8)
	_dat.fill(nodata)

	_dat_r = np.empty([_rows_n, _cols_n], np.uint8)
	_dat_r.fill(0)

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

			_row_min = int(math.ceil(_row_min_f))
			_row_min = max(0, _row_min)

			_col_min = int(math.ceil(_col_min_f))
			_col_min = max(0, _col_min)

			_row_max = int(math.floor(_row_max_f))
			_row_max = min(_rows_o, _row_max)

			_col_max = int(math.floor(_col_max_f))
			_col_max = min(_cols_o, _col_max)

			_ct = 0
			_vs = {}
			for _row_o from _row_min<=_row_o<_row_max:
				for _col_o from _col_min<=_col_o<_col_max:
					_v = dat[_row_o, _col_o]
					if _v == nodata:
						continue

					_vs[_v] = _vs.get(_v, 0) + 1
					_ct += 1

			if _ct == 0:
				continue

			_cm = nodata
			_vm = 0

			for _cc in _vs:
				_vv = _vs[_cc]
				if _vv > _vm:
					_cm = _cc
					_vm = _vv

			_dat[_row_n, _col_n] = _cm
			_dat_r[_row_n, _col_n] = int((100 * _vm) / _ct)
	
	return _dat, _dat_r

