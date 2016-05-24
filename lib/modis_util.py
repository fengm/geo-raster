'''
File: modis_util.py
Author: Min Feng
Version: 0.1
Create: 2016-01-26 17:48:00
Description: utilities for handling MODIS data
'''
_div = 1111950.5197665232305861525775064

def tile(x, y):
	"""@ identify MODIS tile for the coordinate

	:x: X
	:y: Y
	:returns: MODIS tile (e.g., h02v02)

	"""
	_h = int((x + 36 / 2 * _div) / _div)
	_v = int((18 / 2 * _div - y) / _div)

	return _h, _v

def pixel(x, y, size=4800):
	"""@todo: calculate MODIS pixel at the given location

	:x: X
	:y: Y
	:returns: col, row

	"""
	_h, _v = tile(x, y)
	return int(size * (x - ((_h - 36 / 2) * _div)) / _div), \
			int(size * ((_v - 18 / 2) * _div - y) / _div)

class modis_info:

	def __init__(self):
		self.div = 1111950.5197665232305861525775064

	def tile(self, x, y):
		_h = (x + 36 / 2 * self.div) / self.div
		_v = (18 / 2 * self.div - y) / self.div

		return 'h%02dv%02d' % (_h, _v)

	def size(self, cell=500):
		return 2400 * 500 / cell

	def pixel(self, x, y, cell=500):
		import math

		_cell = self.div / self.size(cell)
		_col = int(math.floor((x - self.div * math.floor(x / self.div)) / _cell))
		_row = int(math.floor((self.div * math.ceil(y / self.div) - y) / _cell))

		return _col, _row
