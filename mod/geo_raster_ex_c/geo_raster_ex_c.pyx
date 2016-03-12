

import numpy as np
cimport numpy as np
cimport cython
import logging

@cython.boundscheck(False)

def to_dtype(pixel_type):
	import numpy

	if pixel_type == 1:
		return numpy.uint8
	if pixel_type == 2:
		return numpy.uint16
	if pixel_type == 3:
		return numpy.int16
	if pixel_type == 4:
		return numpy.uint32
	if pixel_type == 5:
		return numpy.int32
	if pixel_type == 6:
		return numpy.float32
	if pixel_type == 7:
		return numpy.float64

	raise Exception('unknown pixel type ' + pixel_type)

cdef to_cell(tuple g, float x, float y):
	'''Convert coordinate to col and row'''
	return int((x - g[0]) / g[1]), int((y - g[3]) / g[5])

def read_block_uint8(np.ndarray[np.uint8_t, ndim=2] dat, ext, prj, geo, int nodata, 
		int row_start, np.ndarray[np.uint8_t, ndim=2] dat_out, min_val=None, max_val=None):
	cdef int _row, _col
	cdef float _x, _y
	cdef int _c, _r

	cdef int _rows_in = dat.shape[0]
	cdef int _cols_in = dat.shape[1]

	cdef int _rows_ot = dat_out.shape[0]
	cdef int _cols_ot = dat_out.shape[1]

	cdef unsigned int _v, _o

	cdef int _col_min = max(0, ext.minx)
	cdef int _col_max = min(_cols_ot, ext.maxx + 1)
	cdef int _row_min = max(0, ext.miny)
	cdef int _row_max = min(_rows_ot, ext.maxy + 1)

	for _row in xrange(_row_min, _row_max):
		for _col in xrange(_col_min, _col_max):
			_o = dat_out[_row, _col]
			if _o != nodata:
				if (min_val == None or _o >= min_val) and (max_val == None or _o <= max_val):
					continue

			_x, _y = prj.project(_col, _row)

			_c, _r = to_cell(geo, _x, _y)
			_r -= row_start

			if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
				continue

			_v = dat[_r, _c]
			if _v == nodata:
				continue

			# if (min_val != None and _v < min_val):
			# 	continue
			# if (max_val != None and _v > max_val):
			# 	continue

			dat_out[_row, _col] = _v

def read_block_uint16(np.ndarray[np.uint16_t, ndim=2] dat, ext, prj, geo, int nodata, 
		int row_start, np.ndarray[np.uint16_t, ndim=2] dat_out, min_val=None, max_val=None):
	cdef int _row, _col
	cdef float _x, _y
	cdef int _c, _r

	cdef int _rows_in = dat.shape[0]
	cdef int _cols_in = dat.shape[1]

	cdef int _rows_ot = dat_out.shape[0]
	cdef int _cols_ot = dat_out.shape[1]

	cdef unsigned short _v, _o

	cdef int _col_min = max(0, ext.minx)
	cdef int _col_max = min(_cols_ot, ext.maxx + 1)
	cdef int _row_min = max(0, ext.miny)
	cdef int _row_max = min(_rows_ot, ext.maxy + 1)

	for _row in xrange(_row_min, _row_max):
		for _col in xrange(_col_min, _col_max):
			_o = dat_out[_row, _col]
			if _o != nodata:
				if (min_val == None or _o >= min_val) and (max_val == None or _o <= max_val):
					continue

			_x, _y = prj.project(_col, _row)

			_c, _r = to_cell(geo, _x, _y)
			_r -= row_start

			if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
				continue

			_v = dat[_r, _c]
			if _v == nodata:
				continue

			# if (min_val != None and _v < min_val):
			# 	continue
			# if (max_val != None and _v > max_val):
			# 	continue

			dat_out[_row, _col] = _v

def read_block_int16(np.ndarray[np.int16_t, ndim=2] dat, ext, prj, geo, int nodata, 
		int row_start, np.ndarray[np.int16_t, ndim=2] dat_out, min_val=None, max_val=None):
	cdef int _row, _col
	cdef float _x, _y
	cdef int _c, _r

	cdef int _rows_in = dat.shape[0]
	cdef int _cols_in = dat.shape[1]

	cdef int _rows_ot = dat_out.shape[0]
	cdef int _cols_ot = dat_out.shape[1]

	cdef short _v, _o

	cdef int _col_min = max(0, ext.minx)
	cdef int _col_max = min(_cols_ot, ext.maxx + 1)
	cdef int _row_min = max(0, ext.miny)
	cdef int _row_max = min(_rows_ot, ext.maxy + 1)

	for _row in xrange(_row_min, _row_max):
		for _col in xrange(_col_min, _col_max):
			_o = dat_out[_row, _col]
			if _o != nodata:
				if (min_val == None or _o >= min_val) and (max_val == None or _o <= max_val):
					continue

			_x, _y = prj.project(_col, _row)

			_c, _r = to_cell(geo, _x, _y)
			_r -= row_start

			if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
				continue

			_v = dat[_r, _c]
			if _v == nodata:
				continue

			# if (min_val != None and _v < min_val):
			# 	continue
			# if (max_val != None and _v > max_val):
			# 	continue

			dat_out[_row, _col] = _v

def read_block_uint32(np.ndarray[np.uint32_t, ndim=2] dat, ext, prj, geo, int nodata, 
		int row_start, np.ndarray[np.uint32_t, ndim=2] dat_out, min_val=None, max_val=None):
	cdef int _row, _col
	cdef float _x, _y
	cdef int _c, _r

	cdef int _rows_in = dat.shape[0]
	cdef int _cols_in = dat.shape[1]

	cdef int _rows_ot = dat_out.shape[0]
	cdef int _cols_ot = dat_out.shape[1]

	cdef unsigned int _v, _o

	cdef int _col_min = max(0, ext.minx)
	cdef int _col_max = min(_cols_ot, ext.maxx + 1)
	cdef int _row_min = max(0, ext.miny)
	cdef int _row_max = min(_rows_ot, ext.maxy + 1)

	for _row in xrange(_row_min, _row_max):
		for _col in xrange(_col_min, _col_max):
			_o = dat_out[_row, _col]
			if _o != nodata:
				if (min_val == None or _o >= min_val) and (max_val == None or _o <= max_val):
					continue

			_x, _y = prj.project(_col, _row)

			_c, _r = to_cell(geo, _x, _y)
			_r -= row_start

			if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
				continue

			_v = dat[_r, _c]
			if _v == nodata:
				continue

			# if (min_val != None and _v < min_val):
			# 	continue
			# if (max_val != None and _v > max_val):
			# 	continue

			dat_out[_row, _col] = _v

def read_block_int32(np.ndarray[np.int32_t, ndim=2] dat, ext, prj, geo, int nodata, 
		int row_start, np.ndarray[np.int32_t, ndim=2] dat_out, min_val=None, max_val=None):
	cdef int _row, _col
	cdef float _x, _y
	cdef int _c, _r

	cdef int _rows_in = dat.shape[0]
	cdef int _cols_in = dat.shape[1]

	cdef int _rows_ot = dat_out.shape[0]
	cdef int _cols_ot = dat_out.shape[1]

	cdef int _v, _o

	cdef int _col_min = max(0, ext.minx)
	cdef int _col_max = min(_cols_ot, ext.maxx + 1)
	cdef int _row_min = max(0, ext.miny)
	cdef int _row_max = min(_rows_ot, ext.maxy + 1)

	for _row in xrange(_row_min, _row_max):
		for _col in xrange(_col_min, _col_max):
			_o = dat_out[_row, _col]
			if _o != nodata:
				if (min_val == None or _o >= min_val) and (max_val == None or _o <= max_val):
					continue

			_x, _y = prj.project(_col, _row)

			_c, _r = to_cell(geo, _x, _y)
			_r -= row_start

			if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
				continue

			_v = dat[_r, _c]
			if _v == nodata:
				continue

			# if (min_val != None and _v < min_val):
			# 	continue
			# if (max_val != None and _v > max_val):
			# 	continue

			dat_out[_row, _col] = _v

def read_block_float32(np.ndarray[np.float32_t, ndim=2] dat, ext, prj, geo, float nodata, 
		int row_start, np.ndarray[np.float32_t, ndim=2] dat_out, min_val=None, max_val=None):
	cdef int _row, _col
	cdef float _x, _y
	cdef int _c, _r

	cdef int _rows_in = dat.shape[0]
	cdef int _cols_in = dat.shape[1]

	cdef int _rows_ot = dat_out.shape[0]
	cdef int _cols_ot = dat_out.shape[1]

	cdef float _v, _o

	cdef int _col_min = max(0, ext.minx)
	cdef int _col_max = min(_cols_ot, ext.maxx + 1)
	cdef int _row_min = max(0, ext.miny)
	cdef int _row_max = min(_rows_ot, ext.maxy + 1)

	for _row in xrange(_row_min, _row_max):
		for _col in xrange(_col_min, _col_max):
			_o = dat_out[_row, _col]
			if _o != nodata:
				if (min_val == None or _o >= min_val) and (max_val == None or _o <= max_val):
					continue

			_x, _y = prj.project(_col, _row)

			_c, _r = to_cell(geo, _x, _y)
			_r -= row_start

			if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
				continue

			_v = dat[_r, _c]
			if _v == nodata:
				continue

			# if (min_val != None and _v < min_val):
			# 	continue
			# if (max_val != None and _v > max_val):
			# 	continue

			dat_out[_row, _col] = _v

class geo_extent:

	@classmethod
	def from_raster(cls, img):
		_geo = img.geo_transform

		_pt1 = (_geo[0], _geo[3])
		_pt2 = (_geo[0] + img.width * _geo[1] + img.height * _geo[2], _geo[3] + img.width * _geo[4] + img.height * _geo[5])

		return cls(_pt1[0], _pt2[1], _pt2[0], _pt1[1], img.proj)

	def __init__(self, x1=-180, y1=-90, x2=180, y2=90, proj=None):
		self.minx = min(x1, x2)
		self.maxx = max(x1, x2)
		self.miny = min(y1, y2)
		self.maxy = max(y1, y2)

		self.proj = proj

	def __str__(self):
		return '%f, %f, %f, %f' % (self.minx, self.miny, self.maxx, self.maxy)

	def width(self):
		return self.maxx - self.minx

	def height(self):
		return self.maxy - self.miny

	def is_intersect(self, extent):
		if extent.maxx < self.minx or \
				extent.minx > self.maxx or \
				extent.maxy < self.miny or \
				extent.miny > self.maxy:
			return False
		return True

	def intersect(self, extent):
		return geo_extent(max(self.minx, extent.minx), max(self.miny, extent.miny), min(self.maxx, extent.maxx), min(self.maxy, extent.maxy), self.proj)

	def union(self, extent):
		return geo_extent(min(self.minx, extent.minx), min(self.miny, extent.miny), max(self.maxx, extent.maxx), max(self.maxy, extent.maxy), self.proj)

	def get_center(self):
		return geo_point(self.minx + self.width() / 2, self.miny + self.height() / 2, self.proj)

	def to_polygon(self):
		_pts = [
				geo_point(self.minx, self.miny),
				geo_point(self.minx, self.maxy),
				geo_point(self.maxx, self.maxy),
				geo_point(self.maxx, self.miny),
				]
		return geo_polygon.from_pts(_pts, self.proj)

class geo_polygon:

	def __init__(self, poly):
		self.poly = poly
		self.proj = poly.GetSpatialReference() if poly != None else None

	@classmethod
	def from_raster(cls, img, div=10):
		_ext = geo_extent.from_raster(img)

		_dis_x = _ext.width()
		_dis_y = _ext.height()

		_cel_x = _dis_x / float(div)
		_cel_y = _dis_y / float(div)

		_pts = [geo_point(_ext.minx, _ext.maxy)]

		for _c in xrange(div):
			_pts.append(geo_point(_ext.minx + _cel_x * (_c+1), _ext.maxy))

		for _c in xrange(div):
			_pts.append(geo_point(_ext.maxx, _ext.maxy - _cel_y * (_c+1)))

		for _c in xrange(div):
			_pts.append(geo_point(_ext.maxx - _cel_x * (_c+1), _ext.miny))

		for _c in xrange(div):
			_pts.append(geo_point(_ext.minx, _ext.miny + _cel_y * (_c+1)))

		return cls.from_pts(_pts, img.proj)

	@classmethod
	def from_raster_location(cls, img, pt):
		_pt = pt.project_to(img.proj)
		_cell = img.to_cell(_pt.x, _pt.y)
		return cls.from_raster_cell(img, _cell[0], _cell[1])

	@classmethod
	def from_raster_cell(cls, img, col, row):
		_trans = img.geo_transform
		_cell_x = _trans[1] / 2
		_cell_y = _trans[5] / 2

		_pt0 = img.to_location(col, row)
		_pts = [
				geo_point(_pt0[0] - _cell_x, _pt0[1] - _cell_y),
				geo_point(_pt0[0] - _cell_x, _pt0[1] + _cell_y),
				geo_point(_pt0[0] + _cell_x, _pt0[1] + _cell_y),
				geo_point(_pt0[0] + _cell_x, _pt0[1] - _cell_y)
				]

		# return cls.from_pts(_pts, img.proj)
		return cls.from_pts(_pts, img.proj)

	@classmethod
	def from_pts(cls, pts, proj=None):
		from osgeo import ogr

		_proj = proj
		_ring = ogr.Geometry(ogr.wkbLinearRing)
		for _pt in pts:
			_ring.AddPoint(_pt.x, _pt.y)
			if _proj != None and _pt.proj != None:
				_proj = _pt.proj
		_ring.CloseRings()

		_poly = ogr.Geometry(ogr.wkbPolygon)
		_poly.AddGeometry(_ring)
		_proj and _poly.AssignSpatialReference(_proj)

		return cls(_poly)

	def project_to(self, proj):
		if self.proj == None or self.proj.IsSame(proj):
			return self

		_poly = self.poly.Clone()
		_err = _poly.TransformTo(proj)

		if _err != 0:
			logging.error('failed to project polygon to (%s)' % (proj.ExportToProj4(), ))
			return None

		return geo_polygon(_poly)

	def set_proj(self, proj):
		self.poly.AssignSpatialReference(proj)
		self.proj = proj

	def union(self, poly):
		return geo_polygon(self.poly.Union(poly.poly))

	def intersect(self, poly):
		return geo_polygon(self.poly.Intersection(poly.poly))

	def center(self):
		_pt = self.poly.Centroid().GetPoint_2D()
		return geo_point(_pt[0], _pt[1], self.poly.GetSpatialReference())

	def extent(self):
		_ext = self.poly.GetEnvelope()
		return geo_extent(_ext[0], _ext[2], _ext[1], _ext[3], self.poly.GetSpatialReference())

	def area(self):
		return self.poly.GetArea()

	def is_intersect(self, poly):
		_poly1 = self.poly
		_poly2 = poly.poly

		return _poly1.Intersect(_poly2)

	def buffer(self, dis):
		_poly = geo_polygon(self.poly.Buffer(dis))
		if self.proj != None:
			_poly.set_proj(self.proj)
		return _poly

	def is_contain(self, pt):
		_loc = pt.project_to(self.proj)

		from osgeo import ogr
		_pt = ogr.Geometry(ogr.wkbPoint)
		_pt.SetPoint_2D(0, _loc.x, _loc.y)

		return self.poly.Contains(_pt)

class projection_transform:
	''' Build a grid for transforming raster pixels'''

	@classmethod
	def from_band(cls, bnd_info, proj, interval=100):
		import math, geo_raster_c

		# make sure there are at least 10 points for each axis
		_scale = min((bnd_info.width / 10.0, bnd_info.height / 10.0, float(interval)))
		assert(_scale > 0)

		_img_w = int(math.ceil(bnd_info.width / _scale)) + 1
		_img_h = int(math.ceil(bnd_info.height / _scale)) + 1

		_ms = []

		# output the points for debugging
		# _pts0 = []
		# _pts1 = []
		for _row in xrange(_img_h):
			_mm = []
			for _col in xrange(_img_w):
				_pt0 = geo_raster_c.to_location(bnd_info.geo_transform, _col * _scale, _row * _scale)
				_pt0 = geo_point(_pt0[0], _pt0[1], bnd_info.proj)
				_pt1 = _pt0.project_to(proj)
				_mm.append([_pt0.x, _pt0.y, _pt1.x, _pt1.y])

				# _pts0.append(_pt0)
				# _pts1.append(_pt1)
			_ms.append(_mm)

		# the function has been moved to geo_base module
		# output_points(_pts0, 'point0.shp')
		# output_points(_pts1, 'point1.shp')

		return cls(_ms, _scale)

	@classmethod
	def from_extent(cls, ext, proj, dist=1000.0):
		import math

		# make sure there are at least 10 points for each axis
		_scale = min((ext.width() / 10.0, ext.height() / 10.0, float(dist)))
		assert(_scale > 0)

		_img_w = int(math.ceil(ext.width() / _scale)) + 1
		_img_h = int(math.ceil(ext.height() / _scale)) + 1

		_ms = []
		_y = ext.miny
		for _row in xrange(_img_h):
			_mm = []
			_x = ext.minx
			for _col in xrange(_img_w):
				_pt0 = geo_point(_x, _y, ext.proj)
				_pt1 = _pt0.project_to(proj)
				_mm.append([_pt0.x, _pt0.y, _pt1.x, _pt1.y])

				_x += dist

			_ms.append(_mm)
			_y += dist

		return cls(_ms, _scale)

	def __init__(self, mat, scale):
		self.mat = mat
		self.scale = float(scale)

	def project(self, int col, int row):
		cdef float _scale = self.scale
		cdef int _col0 = int(col / _scale)
		cdef int _row0 = int(row / _scale)

		cdef int _row1 = _row0 + 1
		cdef int _col1 = _col0 + 1

		cdef float _del_x = col / _scale - _col0
		cdef float _del_y = row / _scale - _row0

		cdef list _mat = self.mat
		# print col, row, _col0, _row0, self.mat.shape
		cdef float _mat_00x = _mat[_row0][_col0][2]
		cdef float _mat_01x = _mat[_row0][_col1][2]
		cdef float _mat_10x = _mat[_row1][_col0][2]
		cdef float _mat_11x = _mat[_row1][_col1][2]

		cdef float _pos_x0 = _mat_00x + _del_x * (_mat_01x - _mat_00x)
		cdef float _pos_x1 = _mat_10x + _del_x * (_mat_11x - _mat_10x)
		cdef float _x = _pos_x0 + (_pos_x1 - _pos_x0) * _del_y

		cdef float _mat_00y = _mat[_row0][_col0][3]
		cdef float _mat_01y = _mat[_row0][_col1][3]
		cdef float _mat_10y = _mat[_row1][_col0][3]
		cdef float _mat_11y = _mat[_row1][_col1][3]

		cdef float _pos_y0 = _mat_00y + _del_y * (_mat_10y - _mat_00y)
		cdef float _pos_y1 = _mat_01y + _del_y * (_mat_11y - _mat_01y)
		cdef float _y = _pos_y0 + (_pos_y1 - _pos_y0) * _del_x

		return _x, _y

class geo_point:
	@classmethod
	def from_raster(cls, raster, col, row):
		_x, _y = raster.to_location(col, row)
		return cls(_x, _y, raster.proj)

	def __init__(self, x, y, proj=None):
		self.put_pt(x, y)
		self.proj = proj

	def put_pt(self, x, y):
		self.x = x
		self.y = y
		self.geom = None

	def get_pt(self):
		return self.x, self.y

	def project_to(self, proj):
		if self.proj == None or self.proj.IsSame(proj):
			return self

		_pt = self.to_geometry()
		_pt.TransformTo(proj)
		_pt = _pt.GetPoint_2D()

		return geo_point(_pt[0], _pt[1], proj=proj)

	def to_geometry(self):
		if self.geom == None:
			from osgeo import ogr
			self.geom = ogr.Geometry(ogr.wkbPoint)

		self.geom.SetPoint_2D(0, self.x, self.y)
		if self.proj != None:
			self.geom.AssignSpatialReference(self.proj)

		return self.geom

	def distance_to(self, pt):
		_pt = pt.project_to(self.proj)
		return ((self.x - _pt.x) ** 2 + (self.y - _pt.y) ** 2) ** 0.5

	def __str__(self):
		return '%f, %f' % (self.x, self.y)

	def __eq__(self, pt):
		if pt == None:
			return False

		return (self.x == pt.x and self.y == pt.y and (self.proj == None or self.proj.IsSame(pt.proj) == 1))

class band_file:

	def __init__(self, f, band_idx=1, dataset_name=None, file_unzip=None):
		self.file = f
		self.dataset_name = dataset_name
		self.band_idx = band_idx
		self.unzip = file_unzip
		self.band = None

	def get_band(self):
		import geo_raster_c

		logging.info('loading %s' % self.file)

		if self.band:
			return self.band

		_img = None
		if self.file.endswith('.gz'):
			if not self.unzip:
				raise Exception('file unzip is required for *.gz files')

			_img = geo_raster_c.geo_raster.open(self.unzip.unzip(self.file))
		else:
			_img = geo_raster_c.geo_raster.open(self.file)

		if _img == None:
			raise Exception('Failed to open image ' + self.file)

		if self.dataset_name:
			_img = _img.get_subdataset(self.dataset_name)
			if _img == None:
				raise Exception('Failed to open dataset ' + \
						self.dataset_name + ' in ' + self.file)

		self.band = _img.get_band(self.band_idx)
		self.band.convert_list = True

		return self.band

	def clean(self):
		self.band = None

class geo_band_obj:

	def __init__(self, poly, bnd_f):
		self.poly = poly
		self.band_file = bnd_f
		self.band = None

	def get_band(self):
		if self.band:
			return self.band

		_bnd = self.band_file.get_band()

		import os
		self.band = geo_band_reader(_bnd, os.path.basename(self.band_file.file))

		return self.band

	def clean(self):
		if self.band:
			self.band.band.clean()
			self.band_file.clean()
			self.band = None

class geo_band_stack_zip:

	def __init__(self, bands, proj=None, check_layers=False, nodata=None):
		if len(bands) == 0:
			raise Exception('the band array is empty')

		self.bands = bands
		_proj = proj
		for _b in bands:
			if _proj == None:
				_proj = _b.poly.proj

		self.last_band = None
		self.proj = _proj
		self.check_layers = check_layers
		self.nodata = nodata
		self.color_table = None
		self.estimate_params_from_band()

		logging.info('build geo_band_stack (bands: %s, nodata: %s -> %s)' % (len(bands), nodata, self.nodata))

	def estimate_params_from_band(self):
		if len(self.bands) == 0:
			raise Exception('No band loaded')

		_bnd = self.bands[0].get_band()

		if self.nodata == None:
			self.nodata = _bnd.band.nodata

		self.pixel_type = _bnd.band.pixel_type
		self.cell_size = _bnd.band.geo_transform[1]
		self.cell_size_y = _bnd.band.geo_transform[5]
		self.color_table = _bnd.band.color_table
		self.bands[0].clean()

	@staticmethod
	def from_list(cls, f_list, band_idx=1, dataset_name=None, \
			file_unzip=None, check_layers=False, nodata=None):
		import geo_base_c as gb

		_bnds = []
		_proj = None
		for _f in f_list:
			_file = _f.strip() if _f else None
			if not _file:
				continue

			# support dataset name from the file path
			_name = dataset_name
			if (not _name) and '#' in _file:
				_ns = _file.split('#')
				_file = _ns[0]
				_name = _ns[1]

			_bnd = band_file(_file, band_idx, _name, file_unzip)
			_bbb = _bnd.get_band()
			assert(_bbb != None)

			if _proj == None:
				_proj = _bbb.proj

			_poly = gb.geo_polygon.from_raster(_bbb)
			_bnds.append(geo_band_obj(_poly, _bnd))

		if len(_bnds) == 0:
			logging.error('No images found')
			return None

		return geo_band_stack_zip(_bnds, _proj, check_layers, nodata)

	@staticmethod
	def from_shapefile(f_list, band_idx=1, dataset_name=None, \
			file_unzip=None, check_layers=False, nodata=None):
		from osgeo import ogr
		import geo_base_c as gb

		_bnds = []
		_shp = ogr.Open(f_list)
		if _shp == None:
			logging.error('failed to load shapefile (%s)' % f_list)
			raise Exception('Failed to load shapefile ' + f_list)

		_lyr = _shp.GetLayer()

		import os
		_d_shp = os.path.dirname(f_list)

		_file_columns = [_col.name for _col in _lyr.schema if _col.name.lower() == 'file']
		if len(_file_columns) != 1:
			raise Exception('failed to find the FILE column in the shapefile (%s)' % \
					','.join([_col.name for _col in _lyr.schema]))

		for _f in _lyr:
			_poly = gb.geo_polygon(_f.geometry().Clone())
			_file = _f.items()[_file_columns[0]]
			_file = _file.strip() if _file else None
			if not _file:
				continue

			if not (_file[0] == '/' or _file[1] == ':'):
				# handle relative path
				_file = _d_shp + os.sep + _file

			# support dataset name from the file path
			_name = dataset_name
			if (not _name) and '#' in _file:
				_ns = _file.split('#')
				_file = _ns[0]
				_name = _ns[1]

			_bnds.append(geo_band_obj(_poly, band_file(_file,
				band_idx, _name, file_unzip)))

		if len(_bnds) == 0:
			logging.error('No images found')
			return None

		return geo_band_stack_zip(_bnds, _lyr.GetSpatialRef(), check_layers, nodata)

	def clean(self):
		for _b in self.bands:
			if _b.band != None:
				_b.clean()

	def get_band(self, pt):
		if self.last_band != None and self.bands[self.last_band].poly.is_contain(pt):
			return self.bands[self.last_band].get_band()

		for i in xrange(len(self.bands)):
			if i == self.last_band:
				continue

			if self.bands[i].poly.is_contain(pt):
				self.last_band = i
				return self.bands[i].get_band()

		return None

	def get_band_xy(self, float x, float y):
		_pt = geo_point(x, y)
		if self.last_band != None and self.bands[self.last_band].poly.is_contain(_pt):
			return self.bands[self.last_band].get_band()

		for i in xrange(len(self.bands)):
			if i == self.last_band:
				continue

			if self.bands[i].poly.is_contain(_pt):
				self.last_band = i
				return self.bands[i].get_band()
		return None

	def read_xy(self, float x, float y, cache=False):
		_v = None
		if self.last_band != None:
			_v = self.bands[self.last_band].get_band().read(x, y, cache)
			if _v != None:
				return _v

		_pt = geo_point(x, y)
		for i in xrange(len(self.bands)):
			if i == self.last_band:
				continue

			if not self.bands[i].poly.is_contain(_pt):
				continue

			_v = self.bands[i].get_band().read(x, y, cache)
			if self.check_layers == False or _v != None:
				self.last_band = i
				return _v

		return None

	def read(self, pt, cache=False):
		_v = None
		if self.last_band != None:
			_v = self.bands[self.last_band].get_band(
						).read_point(pt, cache)

			if _v != None:
				return _v

		for i in xrange(len(self.bands)):
			if i == self.last_band:
				continue

			if not self.bands[i].poly.is_contain(pt):
				continue

			_v = self.bands[i].get_band().read_point(pt, cache)
			if self.check_layers == False or _v != None:
				self.last_band = i
				return _v

		return None

	def get_bands(self, poly):
		_poly = poly.project_to(self.proj)

		_ls = []
		for i in xrange(len(self.bands)):
			if self.bands[i].poly.is_intersect(_poly):
				_ls.append(self.bands[i])

		return _ls

	def get_bands_pts(self, pts):
		if len(pts) == 0:
			logging.warning('no point provided')
			return None

		_ls = []
		for i in xrange(len(self.bands)):
			for _pt in pts:
				if self.bands[i].poly.is_contain(_pt):
					logging.info('add band %s' % self.bands[i].band_file.file)
					_ls.append(self.bands[i])
					break

		return _ls

	def _read_band(self, bnd, bnd_info, nodata, pol_t1, dat_out, min_val=None, max_val=None):
		import geo_base_c as gb

		_bnd_info = bnd_info
		_nodata = nodata
		_dat_out = dat_out
		_pol_t1 = pol_t1

		_bnd = _bnd_info.get_band().band
		logging.info('loading file %s' % _bnd_info.band_file.file)
		_pol_s = gb.geo_polygon.from_raster(_bnd, div=100)

		if _pol_s == None:
			logging.info('skip file #1 %s' % _bnd_info.band_file.file)
			return

		# calculate the intersection area for both data sets
		_pol_t1_proj = _pol_t1.project_to(_bnd.proj)
		if _pol_t1_proj == None or _pol_t1_proj.poly == None:
			logging.info('skip file #2 %s' % _bnd_info.band_file.file)
			return

		# if 'p166r061_20000223' in _bnd_info.band_file.file:
		# 	import geo_base_c as gb
		# 	_ttt = _pol_s.buffer(0.00000001).intersect(_pol_t1_proj)
		# 	print _ttt
		# 	print _ttt.poly
		# 	gb.output_polygons([_pol_s, _pol_t1_proj], 
		# 			'/data/glcf-nx-002/data/PALSAR/water/region/country3/raw4/test2.shp')

		if not _pol_s.extent().is_intersect(_pol_t1_proj.extent()):
			return

		_pol_c_s = _pol_s.intersect(_pol_t1_proj)
		if _pol_c_s.poly == None:
			_pol_c_s = _pol_s.buffer(0.000000001).intersect(_pol_t1_proj)

		if _pol_c_s.poly == None:
			logging.info('skip file #3 %s' % _bnd_info.band_file.file)
			return

		_pol_c_s.set_proj(_bnd.proj)
		_pol_c_t = _pol_c_s.project_to(bnd.proj)

		if _pol_c_t == None or _pol_c_t.poly == None:
			logging.info('failed to reproject the extent')
			return

		#_pol_c_t = _pol_c_t.buffer(bnd.geo_transform[1])
		#print _pol_c_t.proj.ExportToProj4()
		#_pol_c_s = _pol_c_t.project_to(_bnd.proj)

		_ext_s = _pol_c_s.extent()
		_ext_t = _pol_c_t.extent()

		# the rows that contain the intersection area
		_col_s_s, _row_s_s = _bnd.to_cell(_ext_s.minx, _ext_s.maxy)
		_col_s_e, _row_s_e = _bnd.to_cell(_ext_s.maxx, _ext_s.miny)

		if _row_s_s > _row_s_e:
			_row_s_s, _row_s_e = _row_s_e, _row_s_s

		if _row_s_s >= _row_s_e:
			return

		# _col_s_s, _col_s_e = max(0, _col_s_s-1), min(_bnd.width, _col_s_e+1)
		# _row_s_s, _row_s_e = max(0, _row_s_s-1), min(_bnd.height,_row_s_e+1)

		_ext_s_cs = geo_extent(_col_s_s, _row_s_s, _col_s_e, _row_s_e)

		# only load the intersection area to reduce memory use
		_row_s_s = max(0, _row_s_s - 1)

		_dat = _bnd.read_rows(_row_s_s,
				min(_row_s_e + 2, _bnd.height) - _row_s_s)

		_col_t_s, _row_t_s = to_cell(tuple(bnd.geo_transform),
				_ext_t.minx, _ext_t.maxy)
		_col_t_e, _row_t_e = to_cell(tuple(bnd.geo_transform),
				_ext_t.maxx, _ext_t.miny)

		#_col_t_s, _col_t_e = max(0, _col_t_s-1), min(bnd.width, _col_t_e+1)
		#_row_t_s, _row_t_e = max(0, _row_t_s-1), min(bnd.height,_row_t_e+1)
		_ext_t_cs = geo_extent(_col_t_s, _row_t_s, _col_t_e, _row_t_e)

		_prj = projection_transform.from_band(bnd, _bnd.proj)

		if self.pixel_type == 1:
			read_block_uint8(_dat, _ext_t_cs, _prj, _bnd.geo_transform,
					_nodata, _row_s_s, _dat_out, min_val, max_val)
		elif self.pixel_type == 2:
			read_block_uint16(_dat, _ext_t_cs, _prj, _bnd.geo_transform,
					_nodata, _row_s_s, _dat_out, min_val, max_val)
		elif self.pixel_type == 3:
			read_block_int16(_dat, _ext_t_cs, _prj, _bnd.geo_transform,
					_nodata, _row_s_s, _dat_out, min_val, max_val)
		elif self.pixel_type == 4:
			read_block_uint32(_dat, _ext_t_cs, _prj, _bnd.geo_transform,
					_nodata, _row_s_s, _dat_out, min_val, max_val)
		elif self.pixel_type == 5:
			read_block_int32(_dat, _ext_t_cs, _prj, _bnd.geo_transform,
					_nodata, _row_s_s, _dat_out, min_val, max_val)
		elif self.pixel_type == 6:
			read_block_float32(_dat, _ext_t_cs, _prj, _bnd.geo_transform,
					_nodata, _row_s_s, _dat_out, min_val, max_val)
		else:
			raise Exception('The pixel type is not supported ' + \
					str(self.pixel_type))

	def read_block(self, bnd, use_pts=False, min_val=None, max_val=None):
		_default_nodata = {1: 255, 2: 65535, 3: -9999, 4: (2 ** 32) - 1, 5: -9999, 6: -9999}
		if self.pixel_type not in _default_nodata.keys():
			raise Exception('Unsupport data type %s' % self.pixel_type)

		_dat_out = np.empty([bnd.height, bnd.width], dtype=to_dtype(self.pixel_type))

		_nodata = self.nodata
		if _nodata == None:
			_nodata = _default_nodata[self.pixel_type]
			logging.warning('No nodata value provided, using default value (%s)' % _nodata)
	
		_dat_out.fill(_nodata)

		logging.info('reading block from "%s" to "%s"' % (\
			self.proj.ExportToProj4(),
			bnd.proj.ExportToProj4()))

		import geo_base_c as gb
		_pol_t1 = gb.geo_polygon.from_raster(bnd, div=100)
		if _pol_t1 == None or _pol_t1.poly == None:
			return None

		_pol_t2 = _pol_t1.project_to(self.proj)
		if _pol_t2 == None or _pol_t2.poly == None:
			return None

		if use_pts:
			logging.info('enable using PTS')

			_pts_t1 = _pol_t1.get_points(self.proj)
			_bnds = self.get_bands_pts(_pts_t1)
		else:
			_bnds = self.get_bands(_pol_t2)

		logging.info('found %s bands' % len(_bnds))
		print min_val, max_val

		for _bnd_info in _bnds:
			self._read_band(bnd, _bnd_info, _nodata, _pol_t1, _dat_out, min_val, max_val)
			
			_bnd_info.clean()

		import geo_raster_c
		return geo_raster_c.geo_band_cache(_dat_out, bnd.geo_transform, bnd.proj, _nodata, self.pixel_type)

class geo_band_reader:

	def __init__(self, band, name=None):
		self.name = name
		self.band = band
		self.raster = band.raster

		import geo_base_c as gb
		self.poly = gb.geo_polygon.from_raster(self.raster)

	def read(self, float x, float y, cache=False):
		_val = self.band.read_location_cache(x, y) if cache else self.band.read_location(x, y)

		if _val == None or _val == self.band.nodata:
			return None

		return _val

	def read_point(self, pt, cache=False):
		_pt = pt.project_to(self.raster.proj)
		if _pt == None:
			return None

		return self.read(_pt.x, _pt.y, cache)

	def read_polygon(self, poly):
		_poly = poly.project_to(self.poly.proj)
		_env = _poly.extent()

		_cell_x = abs(self.raster.geo_transform[1])
		_cell_y = abs(self.raster.geo_transform[5])

		_vs = []
		for _row in xrange(int(_env.height() / _cell_y)):
			for _col in xrange(int(_env.width() / _cell_x)):
				_x = _env.minx + _cell_x * (_col + 0.5)
				_y = _env.miny + _cell_y * (_row + 0.5)

				if not _poly.is_contain(geo_point(_x, _y)):
					continue

				_v = self.band.read_location(_x, _y)
				if _v == None or _v == self.band.nodata:
					continue

				_vs.append(_v)

		if not len(_vs):
			return None, 0

		return sum(_vs) / len(_vs), max(_vs) - min(_vs)

	def read_ext(self, pt, dist=1):
		_v_o = self.read_point(pt)
		if _v_o == None:
			return None, 0

		_col_o, _row_o = self.raster.to_cell(pt.x, pt.y)
		_vs = []
		for _row in xrange(_row_o - dist, _row_o + dist + 1):
			for _col in xrange(_col_o - dist, _col_o + dist + 1):
				if 0 <= _row < self.band.height and 0 <= _col < self.band.width:
					_v = self.band.read_cell(_col, _row)
					if _v == None or _v == self.banGetAread.nodata:
						continue

					_vs.append(_v)

		return _v_o, max(_vs) - min(_vs)

def collect_samples(bnd_landsat, proj, interval=3000):
	_img_landsat = bnd_landsat.raster
	_read_landsat = geo_band_reader(bnd_landsat)

	import geo_base_c as gb
	_poly_union = gb.geo_polygon.from_raster(_img_landsat).project_to(proj)
	_ext_union = _poly_union.extent()

	_vs = []
	for _row in xrange(abs(int(_ext_union.height() / interval))):
		for _col in xrange(abs(int(_ext_union.width() / interval))):
			_y = _ext_union.miny + interval * (0.5 + _row)
			_x = _ext_union.minx + interval * (0.5 + _col)

			if not _poly_union.is_contain(_x, _y): continue

			_pt = geo_point(_x, _y, proj)
			_vl = _read_landsat.read_point(_pt)

			if None == _vl:
				continue

			_vs.append(_pt)

	return _vs

def modis_projection():
	from osgeo import osr

	_modis_proj = osr.SpatialReference()
	_modis_proj.ImportFromProj4('+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs')

	return _modis_proj

