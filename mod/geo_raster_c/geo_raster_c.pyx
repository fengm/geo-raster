'''
File: geo_raster_c.pyx
Author: Min Feng
Version: 1.0
Create: 2011-05-14
Description: GeoRaster module, define classes for raster and band operations
'''
'''
Version: 1.1
Date: 2013-03-14
Note: add support to geo_band_cache
'''

from osgeo import gdal, ogr, osr
import re
import logging

import numpy as np
cimport numpy as np
cimport cython
import math

@cython.boundscheck(False)

cdef unsigned int read_pixel_ubyte(np.ndarray[np.uint8_t, ndim=2] dat, int row, int col) except *:
	return dat[row, col]

cdef int read_pixel_byte(np.ndarray[np.int8_t, ndim=2] dat, int row, int col) except *:
	return dat[row, col]

cdef unsigned short read_pixel_uint16(np.ndarray[np.uint16_t, ndim=2] dat, int row, int col) except *:
	return dat[row, col]

cdef short read_pixel_int16(np.ndarray[np.int16_t, ndim=2] dat, int row, int col) except *:
	return dat[row, col]

cdef unsigned int read_pixel_uint32(np.ndarray[np.uint32_t, ndim=2] dat, int row, int col) except *:
	return dat[row, col]

cdef int read_pixel_int32(np.ndarray[np.int32_t, ndim=2] dat, int row, int col) except *:
	return dat[row, col]

cdef float read_pixel_float32(np.ndarray[np.float32_t, ndim=2] dat, int row, int col) except *:
	return dat[row, col]

cdef unsigned char write_pixel_byte(np.ndarray[np.uint8_t, ndim=2] dat, int row, int col, unsigned int val) except *:
	dat[row, col] = val

cdef unsigned short write_pixel_uint16(np.ndarray[np.uint16_t, ndim=2] dat, int row, int col, unsigned int val) except *:
	dat[row, col] = val

cdef short write_pixel_int16(np.ndarray[np.int16_t, ndim=2] dat, int row, int col, int val) except *:
	dat[row, col] = val

cdef unsigned int write_pixel_uint32(np.ndarray[np.uint32_t, ndim=2] dat, int row, int col, unsigned int val) except *:
	dat[row, col] = val

cdef int write_pixel_int32(np.ndarray[np.int32_t, ndim=2] dat, int row, int col, int val) except *:
	dat[row, col] = val

cdef float write_pixel_float32(np.ndarray[np.float32_t, ndim=2] dat, int row, int col, float val) except *:
	dat[row, col] = val

cdef int within_extent(int col, int row, int width, int height, int row_start, int row_end):
	if col < 0 or row < 0:
		return 0

	if col >= width or row >= height:
		return 0

	if not (row_start <= row < row_end):
		return 2

	return 1


cdef align_min(val, ref, div):
	import math
	return math.floor((val - ref) / div) * div + ref

cdef align_max(val, ref, div):
	import math
	return math.ceil((val - ref) / div) * div + ref

class geo_raster_info:
	def __init__(self, geo_transform, width, height, proj):
		self.geo_transform = geo_transform
		self.width = width
		self.height = height
		self.proj = proj

	def __del__(self):
		self.geo_transform = None
		self.width = None
		self.height = None
		self.proj = None

	def to_cell(self, float x, float y):
		return to_cell(self.geo_transform, x, y)

	def to_location(self, int col, int row):
		return to_location(self.geo_transform, col, row)

	def extent(self):
		_geo = self.geo_transform

		_pt1 = (_geo[0], _geo[3])
		_pt2 = (_geo[0] + self.width * _geo[1] + self.height * _geo[2], _geo[3] + self.width * _geo[4] + self.height * _geo[5])

		import geo_base_c as gb
		return gb.geo_extent(_pt1[0], _pt2[1], _pt2[0], _pt1[1], self.proj)

	def cell_extent(self, col, row):
		_trans = self.geo_transform

		_cell_x = _trans[1] / 2
		_cell_y = _trans[5] / 2

		_pt0 = self.to_location(col, row)

		import geo_base_c as gb
		return gb.geo_extent(_pt0[0] - _cell_x, _pt0[1] - _cell_y,
					   _pt0[0] + _cell_x, _pt0[1] + _cell_y, self.proj)

class geo_band_info(geo_raster_info):

	def __init__(self, geo_transform, width, height, proj, nodata=None, pixel_type=None):
		geo_raster_info.__init__(self, geo_transform, width, height, proj)
		self.nodata = nodata
		self.pixel_type = pixel_type

	def __del__(self):
		geo_raster_info.__del__(self)

		self.nodata = None
		self.pixel_type = None

	def get_nodata(self):
		_nodata = self.nodata

		if _nodata == None:
			_default_nodata = {1: 255, 2: 65535, 3: -9999, 4: (2 ** 32) - 1, 5: -9999, 6: -9999}
			if self.pixel_type not in _default_nodata.keys():
				raise Exception('Unsupport data type %s' % self.pixel_type)

			_nodata = _default_nodata[self.pixel_type]
			logging.warning('No nodata value provided, using default value (%s)' % _nodata)

		return _nodata

	def from_ma_grid(self, grid, update_type=True, nodata=None):
		logging.info('updating the band with masked array')

		_nodata = nodata
		if _nodata == None:
			_nodata = self.nodata

		if _nodata == None:
			raise Exception('nodata is required')

		_dat = grid.filled(_nodata)
		return self.from_grid(_dat, update_type, _nodata)

	def from_grid(self, grid, update_type=True, nodata=None):
		logging.info('updating the band with masked array')

		if not (self.height == grid.shape[0] and self.width == grid.shape[1]):
			raise Exception('grid size does not match')

		_nodata = nodata
		if _nodata == None:
			_nodata = self.nodata

		_dat = grid

		import geo_base_c as gb
		return geo_band_cache(_dat, list(self.geo_transform), self.proj, _nodata, gb.from_dtype(grid.dtype))

	def sub_band(self, col, row, width, height):
		_geo = list(self.geo_transform)

		_geo[0] += col * _geo[1] + row * _geo[2]
		_geo[3] += col * _geo[4] + row * _geo[5]

		_cols = min(width, self.width - col)
		_rows = min(height, self.height - row)

		if _cols <= 0 or _rows <= 0:
			raise Exception('out of the band extent')

		return geo_band_info(_geo, _cols, _rows, self.proj, self.nodata, self.pixel_type)

	def align(self, ext, clip=False):
		_geo = self.geo_transform

		_cell = _geo[1]

		_s_x = _geo[0]
		if _s_x > ext.minx:
			_s_x -= (int((_s_x - ext.minx) / _cell) + 10)  * _cell

		_s_y = _geo[3]
		if _s_y < ext.maxy:
			_s_y += (int((ext.maxy - _s_y) / _cell) + 10)  * _cell

		_min_x = align_min(ext.minx, _s_x, _cell)
		_max_x = align_max(ext.maxx, _s_x, _cell)

		_min_y = align_max(ext.miny, _s_y, _cell)
		_max_y = align_min(ext.maxy, _s_y, _cell)

		if clip:
			_ref_min_x = _geo[0]
			_ref_max_y = _geo[3]
			_ref_max_x = _geo[0] + _geo[1] * self.width + _geo[2] * self.height
			_ref_min_y = _geo[3] + _geo[4] * self.width + _geo[5] * self.height

			_min_x = max(_ref_min_x, _min_x)
			_min_y = max(_ref_min_y, _min_y)

			_max_x = min(_ref_max_x, _max_x)
			_max_y = min(_ref_max_y, _max_y)

		ext.minx = _min_x
		ext.miny = _min_y
		ext.maxx = _max_x
		ext.maxy = _max_y

		_cols = int(round((_max_x - _min_x) / _cell))
		_rows = int(round((_max_y - _min_y) / _cell))

		return geo_band_info([_min_x, _cell, 0, _max_y, 0, _cell * -1], _cols, _rows, self.proj, self.nodata, self.pixel_type)

class geo_band_cache(geo_band_info):

	def __init__(self, data, geo_transform, proj, nodata=None, pixel_type=None):
		geo_band_info.__init__(self, geo_transform, data.shape[1], data.shape[0], proj, nodata, pixel_type)
		self.data = data

	def __del__(self):
		geo_band_info.__del__(self)
		self.data = None

	@property
	def data_ma(self):
		if self.nodata == None:
			raise Exception('nodata is required')
		return np.ma.masked_equal(self.data, self.nodata)

	def read_location(self, float x, float y):
		'''Read a cell at given coordinate'''
		cdef int _col, _row

		_col, _row = self.to_cell(x, y)
		if _col < 0 or _row < 0 or _col >= self.width or _row >= self.height:
			return None

		return self.read_cell(_col, _row)

	def read_cell(self, int col, int row):
		'''Read a cell at given col/row'''
		cdef int _s = within_extent(col, row, self.width,
				self.height, 0, self.height)

		if _s == 0:
			return None

		if self.data.dtype == np.int8:
			return read_pixel_byte(self.data, row, col)
		elif self.data.dtype == np.uint8:
			return read_pixel_ubyte(self.data, row, col)
		elif self.data.dtype == np.uint16:
			return read_pixel_uint16(self.data, row, col)
		elif self.data.dtype == np.int16:
			return read_pixel_int16(self.data, row, col)
		elif self.data.dtype == np.uint32:
			return read_pixel_uint32(self.data, row, col)
		elif self.data.dtype == np.int32:
			return read_pixel_int32(self.data, row, col)
		elif self.data.dtype == np.float32:
			return read_pixel_float32(self.data, row, col)
		else:
			return self.data[row][col]

		# if self.pixel_type == 1:
		# 	if self.data.dtype == np.int8:
		# 		return read_pixel_byte(self.data, row, col)
		# 	else:
		# 		return read_pixel_ubyte(self.data, row, col)
		# elif self.pixel_type == 2:
		# 	return read_pixel_uint16(self.data, row, col)
		# elif self.pixel_type == 3:
		# 	return read_pixel_int16(self.data, row, col)
		# elif self.pixel_type == 4:
		# 	return read_pixel_uint32(self.data, row, col)
		# elif self.pixel_type == 5:
		# 	return read_pixel_int32(self.data, row, col)
		# elif self.pixel_type == 6:
		# 	return read_pixel_float32(self.data, row, col)
		# else:
		# 	return self.data[row][col]

	def write_cell(self, int col, int row, val):
		'''Write a cell value at given col/row'''
		cdef int _s = within_extent(col, row, self.width,
				self.height, 0, self.height)

		if _s == 0:
			return None

		if self.pixel_type == 1:
			write_pixel_byte(self.data, row, col, val)
		elif self.pixel_type == 2:
			write_pixel_uint16(self.data, row, col, val)
		elif self.pixel_type == 3:
			write_pixel_int16(self.data, row, col, val)
		elif self.pixel_type == 4:
			write_pixel_uint32(self.data, row, col, val)
		elif self.pixel_type == 5:
			write_pixel_int32(self.data, row, col, val)
		elif self.pixel_type == 6:
			write_pixel_float32(self.data, row, col, val)
		else:
			self.data[row][col] = val


	def write(self, f, opts=[]):
		'''write the raster to file'''
		_pixel_type = self.pixel_type
		if _pixel_type == None:
			from osgeo import gdal
			_pixel_type = gdal.GDT_Byte
		write_raster(f, self.geo_transform, self.proj.ExportToWkt(),
				self.data, nodata=self.nodata, pixel_type=_pixel_type, opts=opts)

	def save(self, f, driver='GTiff', color_table=None, opts=[]):
		'''write the raster to file'''
		_pixel_type = self.pixel_type
		if _pixel_type == None:
			from osgeo import gdal
			_pixel_type = gdal.GDT_Byte
		write_raster(f, self.geo_transform, self.proj.ExportToWkt(),
				self.data, nodata=self.nodata, pixel_type=_pixel_type, driver=driver, color_table=color_table, opts=opts)

	def read_ext(self, ext):
		if ext.proj != None and self.proj.ExportToProj4() != ext.proj.ExportToProj4():
			raise Exception('The extent is supposed to be in the same CRS as the band does')

		_ext1 = self.extent()
		if _ext1.minx == ext.minx and _ext1.maxy == ext.maxy and _ext1.maxx == ext.maxx and _ext1.miny == ext.miny:
			# if the band has same size and extent then return without
			# adjustment
			return self

		_geo1 = list(self.geo_transform)
		_cell = _geo1[1]
		_fill = self.get_nodata()

		import math
		_cols = int(math.ceil((ext.width() / _cell)))
		_rows = int(math.ceil((ext.height() / _cell)))

		import numpy
		_dat = numpy.empty((_rows, _cols), dtype=self.data.dtype)
		_dat.fill(_fill)

		import geo_base_c as gb
		_ext = gb.geo_extent.from_raster(self).intersect(ext)

		_off_x1 = int((_ext.minx - _geo1[0]) / _cell)
		_off_y1 = int((_geo1[3] - _ext.maxy) / _cell)

		_off_x2 = int((_ext.minx - ext.minx) / _cell)
		_off_y2 = int((ext.maxy - _ext.maxy) / _cell)

		import math
		_w = int(math.ceil((_ext.width() / _cell)))
		_h = int(math.ceil((_ext.height() / _cell)))

		_dat[_off_y2: _off_y2 + _h, _off_x2: _off_x2 + _w] = \
			self.data[_off_y1: _off_y1 + _h, _off_x1: _off_x1 + _w]

		_geo2 = list(_geo1)

		_geo2[0] = _ext.minx
		_geo2[3] = _ext.maxy

		return geo_band_cache(_dat, _geo2, self.proj, _fill,
						self.pixel_type)

	def read_block(self, bnd):
		import geo_base_c

		_prj = geo_base_c.projection_transform.from_band(bnd, self.proj)

		_pol_t1 = geo_base_c.geo_polygon.from_raster(bnd).segment_ratio(10)
		_pol_t2 = _pol_t1.project_to(self.proj)
		if _pol_t2 == None:
			return None

		_bnd = self
		_pol_s = geo_base_c.geo_polygon.from_raster(_bnd).segment_ratio(10)

		# calculate the intersection area for both data sets
		_pol_c_s = _pol_s.intersect(_pol_t2)
		if _pol_c_s.poly == None:
			logging.warning('The raster does not cover the request bnd')
			return None

		_pol_c_s.set_proj(_bnd.proj)
		_pol_c_t = _pol_c_s.project_to(bnd.proj)

		_ext_s = _pol_c_s.extent()
		_ext_t = _pol_c_t.extent()

		# the rows that contain the intersection area
		_col_s_s, _row_s_s = _bnd.to_cell(_ext_s.minx, _ext_s.maxy)
		_col_s_e, _row_s_e = _bnd.to_cell(_ext_s.maxx, _ext_s.miny)

		# _col_s_s, _col_s_e = max(0, _col_s_s-1), min(_bnd.width, _col_s_e+1)
		# _row_s_s, _row_s_e = max(0, _row_s_s-1), min(_bnd.height,_row_s_e+1)

		_ext_s_cs = geo_base_c.geo_extent(_col_s_s, _row_s_s,
				_col_s_e, _row_s_e)

		_row_s_s = 0
		_dat = _bnd.data

		_col_t_s, _row_t_s = to_cell(tuple(bnd.geo_transform),
				_ext_t.minx, _ext_t.maxy)
		_col_t_e, _row_t_e = to_cell(tuple(bnd.geo_transform),
				_ext_t.maxx, _ext_t.miny)

		_ext_t_cs = geo_base_c.geo_extent(_col_t_s, _row_t_s,
				_col_t_e, _row_t_e)

		_nodata = self.get_nodata()
		_dat_out = np.empty([bnd.height, bnd.width],
				dtype=geo_base_c.to_dtype(self.pixel_type))
		_dat_out.fill(_nodata)

		if self.pixel_type == 1:
			geo_base_c.read_block_uint8(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 2:
			geo_base_c.read_block_uint16(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 3:
			geo_base_c.read_block_int16(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 4:
			geo_base_c.read_block_uint32(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 5:
			geo_base_c.read_block_int32(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 6:
			geo_base_c.read_block_float32(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		else:
			raise Exception('The pixel type is not supported ' + \
					str(self.pixel_type))

		return geo_band_cache(_dat_out, bnd.geo_transform, bnd.proj,
			_nodata, self.pixel_type)

class geo_band(geo_band_info):
	'''A raster band'''

	def __init__(self, raster, band, convert_list=False):
		geo_band_info.__init__(self, raster.geo_transform, band.XSize, band.YSize,
						 raster.projection_obj, band.GetNoDataValue(), band.DataType)

		self.raster = raster
		self.band = band
		self.description = band.GetDescription()
		self.names = band.GetRasterCategoryNames()
		self.size = [self.height, self.width]
		self.data = None
		self.buf_row_start = -1
		self.buf_row_end = -1
		self.buf_col_start = -1
		self.buf_col_end = -1
		self.color_table = band.GetColorTable()
		self.test = None
		self.convert_list = convert_list

	def __del__(self):
		geo_band_info.__del__(self)

		self.raster = None
		self.band = None
		self.description = None
		self.names = None
		self.size = None
		self.color_table = None
		self.clean()

	def clean(self):
		'''clean cached data'''
		self.data = None
		self.buf_row_start = -1
		self.buf_col_start = -1

	def read_location_cache(self, float x, float y):
		'''Read a cell at given coordinate. the entire band is cached to avoid multiple IO'''
		if self.data == None:
			self.read()

		_col, _row = self.raster.to_cell(x, y)
		if _col < 0 or _row < 0 or _col >= self.width or _row >= self.height:
			return None

		return self.data[_row][_col] if self.convert_list \
				else self.data[_row, _col]

	def read_cell_cache(self, int col, int row):
		'''Read a cell at given col/row, the entire band is cached to avoid multiple IO'''
		if col < 0 or row < 0 or col >= self.width or row >= self.height:
			return None

		if self.data == None:
			self.read()

		return self.data[row][col] if self.convert_list \
				else self.data[row, col]

	def read_location(self, float x, float y, int row_num=12):
		'''Read a cell at given coordinate'''

		_col, _row = self.raster.to_cell(x, y)
		return self.read_cell(_col, _row, row_num)


	def is_cached(self, int row):
		if not (0 <= row < self.height):
			return False

		# if self.data== None or self.buf_row_start < 0 or not (self.buf_row_start <= row < self.buf_row_start + self.data.shape[0]):
		if self.data== None or self.buf_row_start < 0 or not \
				(self.buf_row_start <= row < self.buf_row_start + \
				self.data.shape[0]):
			return False

		return True

	def read_cell(self, int col, int row, int row_num=15):
		'''Read a cell at given col/row'''

		cdef int _s = within_extent(col, row, self.width,
				self.height, self.buf_row_start, self.buf_row_end)

		if _s == 0:
			return None
		if _s == 2:
			self.read_rows(max(0, row - row_num / 3), row_num)

		cdef int _row = row - self.buf_row_start
		if self.pixel_type == 1:
			if self.data.dtype == np.int8:
				return read_pixel_byte(self.data, _row, col)
			else:
				return read_pixel_ubyte(self.data, _row, col)
		elif self.pixel_type == 2:
			return read_pixel_uint16(self.data, _row, col)
		elif self.pixel_type == 3:
			return read_pixel_int16(self.data, _row, col)
		elif self.pixel_type == 4:
			return read_pixel_uint32(self.data, _row, col)
		elif self.pixel_type == 5:
			return read_pixel_int32(self.data, _row, col)
		elif self.pixel_type == 6:
			return read_pixel_float32(self.data, _row, col)
		else:
			return self.data[_row][col]

	def read_rows(self, row, row_num=12, col=0, col_num=-1):
		'''Read rows from the raster band and cache them'''

		self.data = None

		_rows = row_num
		if row + _rows > self.height:
			_rows = self.height - row

		_cols = col_num
		if _cols < 0:
			_cols = self.width

		_d = self.band.ReadAsArray(col, row, _cols, _rows, _cols, _rows)
		self.data = _d
		self.buf_row_start = row
		self.buf_row_end = row + _d.shape[0]
		self.buf_col_start = col
		self.buf_col_end = col + _d.shape[1]

		return self.data

	@property
	def cached(self):
		_dat = self.data
		if _dat == None:
			return None

		_geo = list(self.geo_transform)

		_col = self.buf_col_start
		_row = self.buf_row_start
		
		_geo[0] += _col * _geo[1] + _row * _geo[2]
		_geo[3] += _col * _geo[4] + _row * _geo[5]

		return geo_band_cache(_dat, _geo, self.proj, self.nodata, self.pixel_type)

	def read(self):
		'''Read all the raster data'''
		return self.read_rows(0, self.height)

	def write(self, rows, x_offset=0, y_offset=0, flush=True):
		'''Write a block to the band'''
		self.band.WriteArray(rows, x_offset, y_offset)
		if flush:
			self.flush()
			self.raster.flush()

	def flush(self):
		self.band.FlushCache()

	def cache(self):
		_img = self.raster
		_dat = self.read_rows(0, self.height)
		return geo_band_cache(_dat, _img.geo_transform, _img.proj,
				self.nodata, self.pixel_type)

	def read_ext(self, ext):
		if ext.proj != None and self.proj.ExportToProj4() != ext.proj.ExportToProj4():
			raise Exception('The extent is supposed to be in the same CRS as the band does')

		_ext1 = self.extent()
		if _ext1.minx == ext.minx and _ext1.maxy == ext.maxy and _ext1.maxx == ext.maxx and _ext1.miny == ext.miny:
			# if the band has same size and extent then return without
			# adjustment
			return self.cache()

		_geo1 = list(self.geo_transform)
		_cell = _geo1[1]
		_fill = self.get_nodata()

		import math
		_cols = int(math.ceil((ext.width() / _cell)))
		_rows = int(math.ceil((ext.height() / _cell)))

		import numpy
		_dat = numpy.empty((_rows, _cols))
		_dat.fill(_fill)

		import geo_base_c as gb
		_ext = gb.geo_extent.from_raster(self).intersect(ext)

		_off_x1 = int((_ext.minx - _geo1[0]) / _cell)
		_off_y1 = int((_geo1[3] - _ext.maxy) / _cell)

		_off_x2 = int((_ext.minx - ext.minx) / _cell)
		_off_y2 = int((ext.maxy - _ext.maxy) / _cell)

		import math
		_w = int(math.ceil((_ext.width() / _cell)))
		_h = int(math.ceil((_ext.height() / _cell)))

		_dat[_off_y2: _off_y2 + _h, _off_x2: _off_x2 + _w] = \
			self.read_rows(_off_y1, _h)[0: _h, _off_x1: _off_x1 + _w]

		_geo2 = list(_geo1)

		_geo2[0] = _ext.minx
		_geo2[3] = _ext.maxy

		return geo_band_cache(_dat, _geo2, self.proj, _fill,
						self.pixel_type)

	def read_block(self, bnd):
		import geo_base_c

		_prj = geo_base_c.projection_transform.from_band(bnd, self.proj)

		_pol_t1 = geo_base_c.geo_polygon.from_raster(bnd).segment_ratio(10)
		_pol_t2 = _pol_t1.project_to(self.proj)
		if _pol_t2 == None:
			raise Exception('failed to project the grid extent')

		_bnd = self
		_pol_s = geo_base_c.geo_polygon.from_raster(_bnd).segment_ratio(10)

		# calculate the intersection area for both data sets
		_pol_c_s = _pol_s.intersect(_pol_t2)
		if _pol_c_s == None or _pol_c_s.poly == None:
			logging.warning('The raster does not cover the request bnd')
			return None

		_pol_c_s.set_proj(_bnd.proj)
		_pol_c_t = _pol_c_s.project_to(bnd.proj)

		_ext_s = _pol_c_s.extent()
		_ext_t = _pol_c_t.extent()

		# the rows that contain the intersection area
		_col_s_s, _row_s_s = _bnd.to_cell(_ext_s.minx, _ext_s.maxy)
		_col_s_e, _row_s_e = _bnd.to_cell(_ext_s.maxx, _ext_s.miny)

		# _col_s_s, _col_s_e = max(0, _col_s_s-1), min(_bnd.width, _col_s_e+1)
		# _row_s_s, _row_s_e = max(0, _row_s_s-1), min(_bnd.height,_row_s_e+1)

		_ext_s_cs = geo_base_c.geo_extent(_col_s_s, _row_s_s,
				_col_s_e, _row_s_e)

		# only load the intersection area to reduce memory use
		_row_s_s = max(0, _row_s_s - 1)
		_row_num = min(_row_s_e + 2, _bnd.height) - _row_s_s
		if _row_num <= 0:
			logging.warning('The raster does not cover the request bnd')
			return None

		_dat = _bnd.read_rows(_row_s_s, _row_num)

		_col_t_s, _row_t_s = to_cell(tuple(bnd.geo_transform),
				_ext_t.minx, _ext_t.maxy)
		_col_t_e, _row_t_e = to_cell(tuple(bnd.geo_transform),
				_ext_t.maxx, _ext_t.miny)

		_ext_t_cs = geo_base_c.geo_extent(_col_t_s, _row_t_s,
				_col_t_e, _row_t_e)

		_nodata = self.get_nodata()
		_dat_out = np.empty([bnd.height, bnd.width],
				dtype=geo_base_c.to_dtype(self.pixel_type))
		_dat_out.fill(_nodata)

		if self.pixel_type == 1:
			geo_base_c.read_block_uint8(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 2:
			geo_base_c.read_block_uint16(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 3:
			geo_base_c.read_block_int16(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 4:
			geo_base_c.read_block_uint32(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 5:
			geo_base_c.read_block_int32(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		elif self.pixel_type == 6:
			geo_base_c.read_block_float32(_dat, _ext_t_cs, _prj,
					_bnd.geo_transform, _nodata, _row_s_s, _dat_out)
		else:
			raise Exception('The pixel type is not supported ' + \
					str(self.pixel_type))

		return geo_band_cache(_dat_out, bnd.geo_transform, bnd.proj,
			_nodata, self.pixel_type)

class geo_raster(geo_raster_info):

	def __init__(self, f, raster):
		if not raster:
			raise Exception('failed to load raster')

		self.projection = raster.GetProjection()

		_proj = osr.SpatialReference()
		_proj.ImportFromWkt(self.projection)

		_cols = raster.RasterXSize
		_rows = raster.RasterYSize

		geo_raster_info.__init__(self, raster.GetGeoTransform(), _cols, _rows, _proj)

		self.projection_obj = _proj
		self.filepath = f
		self.raster = raster

		self.init_vars()

		_proj = None
		_cols = None
		_rows = None

	def __del__(self):
		geo_raster_info.__del__(self)

		self.projection = None
		self.projection_obj = None
		self.filepath = None
		self.raster = None
		self.band_num = None
		self.size = None
		self.cell_size_x = None
		self.cell_size_y = None
		self.cell_size = None

	@staticmethod
	def open(f, update=False):
		if update:
			_img = gdal.Open(f, gdal.GA_Update)
		else:
			_img = gdal.Open(f)

		if not _img:
			raise Exception('failed to load file ' + f)

		return geo_raster(f, _img)

	@staticmethod
	def create(f, size, geo_transform, proj, pixel_type=gdal.GDT_Byte, driver='GTiff', nodata=None, color_table=None, opts=[]):
		if f.lower().endswith('.img'):
			driver = 'HFA'

		_driver = gdal.GetDriverByName(driver)
		_size = [1] + size if len(size) == 2 else size

		_img = _driver.Create(f, _size[2], _size[1], _size[0], pixel_type, opts)
		for _b in xrange(_size[0]):
			_band = _img.GetRasterBand(_b + 1)

			if nodata != None:
				_band.SetNoDataValue(nodata)
			if color_table != None:
				_band.SetColorTable(color_table)

		_img.SetGeoTransform(geo_transform)

		_prj = proj
		if _prj == None:
			logging.warning('no SRS specified')
		else:
			if type(_prj) != str:
				_prj = proj.ExportToWkt()
			_img.SetProjection(_prj)

		return geo_raster(f, _img)

	def sub_datasets(self):
		return self.raster.GetSubDatasets()

	def get_subdataset(self, band):
		_band = str(band)
		for _n, _d in self.raster.GetSubDatasets():
			if _n.endswith(_band):
				return geo_raster.open(_n.strip())

		return None

	def init_vars(self):
		self.band_num = self.raster.RasterCount
		self.size = [self.band_num, self.height, self.width]
		self.cell_size_x = self.geo_transform[1]
		self.cell_size_y = self.geo_transform[5]
		self.cell_size = self.cell_size_x

	def to_cell(self, x, y):
		return to_cell(self.geo_transform, x, y)

	def to_location(self, col, row):
		return to_location(self.geo_transform, col, row)

	def get_band(self, band_num=1, cache=False):
		if not (1 <= band_num <= self.band_num):
			raise Exception('band index is not availible (bands %d)' % self.band_num)

		_bnd = geo_band(self, self.raster.GetRasterBand(band_num))
		if cache:
			_bnd.read()
		return _bnd

	def save(self, fou, opts=[]):
		if fou.lower().endswith('.img'):
			driver = 'HFA'

		_bnd = self.get_band(1)
		_driver = gdal.GetDriverByName(driver)

		_img = _driver.Create(fou, self.width,
				self.height, self.band_num, _bnd.pixel_type, opts)

		for _b in xrange(self.band_num):
			_bnd_inp = self.get_band(_b + 1)
			_bnd_out = _img.GetRasterBand(_b + 1)

			if _bnd_inp.nodata != None:
				_bnd_out.SetNoDataValue(_bnd_inp.nodata)
			if _bnd_inp.color_table != None:
				_bnd_out.SetColorTable(_bnd_inp.color_table)

			_dat = _bnd_inp.read()

			_bnd_out.WriteArray(_dat)
			_bnd_out.FlushCache()

		_img.SetGeoTransform(self.geo_transform)
		self.projection and _img.SetProjection(self.projection)

	def write_bands(self, img):
		'''Write a 3D block to each band of the image'''
		for _b in xrange(self.band_num):
			_band = self.raster.GetRasterBand(_b + 1)
			_band.WriteArray(img[_b, :, :])
			_band.FlushCache()

	def reproject(self, proj, x, y):
		return self.project_to(proj, x, y)

	def project_to(self, proj, x, y):
		_pt = ogr.Geometry(ogr.wkbPoint)

		_pt.SetPoint_2D(0, x, y)
		_pt.AssignSpatialReference(self.projection_obj)
		_pt.TransformTo(proj)
		_pt = _pt.GetPoint_2D()

		return _pt

	def project_from(self, proj, x, y):
		_pt = ogr.Geometry(ogr.wkbPoint)

		_pt.SetPoint_2D(0, x, y)
		_pt.AssignSpatialReference(proj)
		_pt.TransformTo(self.projection_obj)
		_pt = _pt.GetPoint_2D()

		return _pt

	def flush(self):
		"""Flush the cache for writting"""
		self.raster.FlushCache()

def open(f, update=False):
	return geo_raster.open(f, update)

def write_raster(f, geo_transform, proj, img, pixel_type=gdal.GDT_Byte, driver='GTiff', nodata=None, color_table=None, opts=[]):
	if f.lower().endswith('.img'):
		driver = 'HFA'

	_driver = gdal.GetDriverByName(driver)

	_size = img.shape
	if len(_size) == 2:
		_img = _driver.Create(f, _size[1], _size[0], 1, pixel_type, opts)

		_band = _img.GetRasterBand(1)
		if color_table != None:
			_band.SetColorTable(color_table)
		if nodata != None:
			_band.SetNoDataValue(nodata)
		_band.WriteArray(img)
		_band.FlushCache()
	else:
		_img = _driver.Create(f, _size[2], _size[1], _size[0], pixel_type, opts)
		for _b in xrange(_size[0]):
			_band = _img.GetRasterBand(_b + 1)

			if nodata != None:
				_band.SetNoDataValue(nodata)
			if color_table != None:
				_band.SetColorTable(color_table)
			_band.WriteArray(img[_b, :, :])
			_band.FlushCache()

	_img.SetGeoTransform(geo_transform)

	_prj = proj
	if _prj == None:
		logging.warning('no SRS specified')
	else:
		if type(_prj) != str:
			_prj = proj.ExportToWkt()
		_img.SetProjection(_prj)

def map_colortable(cs):
	_color_tables = gdal.ColorTable()
	for i in xrange(256):
		if i in cs:
			_color_tables.SetColorEntry(i, cs[i])

	return _color_tables

def load_colortable(f):
	import sys

	_colors = {}
	for _l in sys.modules['__builtin__'].open(f).read().splitlines():
		_l = _l.strip()
		if not _l:
			continue

		_vs = re.split('\s+', _l, maxsplit=1)
		if len(_vs) != 2:
			logging.info('ignore color entry: %s' % _l)
			continue

		_cs = tuple([int(_v) for _v in re.split('\W+', _vs[1])])
		if len(_cs) < 3:
			raise Exception('insufficent color values %s' % len(_cs))

		_colors[float(_vs[0])] = _cs

	return map_colortable(_colors)

def pixel_type(t='byte'):
	t = t.lower()

	if t == 'byte': return gdal.GDT_Byte
	if t == 'float': return gdal.GDT_Float32
	if t == 'double': return gdal.GDT_Float64
	if t == 'int': return gdal.GDT_Int32
	if t == 'short': return gdal.GDT_Int16
	if t == 'ushort': return gdal.GDT_UInt16

	raise Exception('unknown type ' + t)

def proj_from_epsg(code=4326):
	_proj = osr.SpatialReference()
	_proj.ImportFromEPSG(code)

	return _proj

def to_cell(g, x, y):
	'''Convert coordinate to col and row'''
	return int((x - g[0]) / g[1]), int((y - g[3]) / g[5])

def to_location(g, col, row):
	'''Convert pixel col/row to the coordinate at the center of the pixel'''
	_col = col + 0.5
	_row = row + 0.5
	return g[0] + g[1] * _col + g[2] * _row, g[3] + g[4] * _col + g[5] * _row
