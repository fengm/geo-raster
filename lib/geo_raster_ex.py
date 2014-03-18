
import logging

class geo_extent:

	@classmethod
	def from_raster(cls, img):
		_geo = img.geo_transform

		_pt1 = (_geo[0], _geo[3])
		_pt2 = (_geo[0] + img.width * _geo[1] + img.height * _geo[2],
				_geo[3] + img.width * _geo[4] + img.height * _geo[5])

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
		self.proj = poly.GetSpatialReference()

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

		# return cls.from_pts(_pts, img.projection_obj)
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
		_poly.TransformTo(proj)

		return geo_polygon(_poly)

	def union(self, poly):
		return geo_polygon(self.poly.Intersection(poly.poly))

	def center(self):
		_pt = self.poly.Centroid().GetPoint_2D()
		return geo_point(_pt[0], _pt[1], self.poly.GetSpatialReference())

	def extent(self):
		_ext = self.poly.GetEnvelope()
		return geo_extent(_ext[0], _ext[2], _ext[1], _ext[3], self.poly.GetSpatialReference())

	def is_intersect(self, poly):
		_poly1 = self.poly
		_poly2 = poly.poly

		return _poly1.Intersect(_poly2)

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
		import math, geo_raster

		_scale = float(interval)

		_img_w = int(math.ceil(bnd_info.width / _scale)) + 1
		_img_h = int(math.ceil(bnd_info.height / _scale)) + 1

		_ms = []
		for _row in xrange(_img_h):
			_mm = []
			for _col in xrange(_img_w):
				_pt0 = geo_raster.to_location(bnd_info.geo_transform, _col * _scale, _row * _scale)
				_pt0 = geo_point(_pt0[0], _pt0[1], bnd_info.proj)
				_pt1 = _pt0.project_to(proj)
				_mm.append([_pt0.x, _pt0.y, _pt1.x, _pt1.y])
			_ms.append(_mm)

		return cls(_ms, _scale)

	@classmethod
	def from_extent(cls, ext, proj, dist=1000.0):
		import math

		_scale = float(dist)

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

	def project(self, col, row):
		_col0 = int(col / self.scale)
		_row0 = int(row / self.scale)

		_row1 = _row0 + 1
		_col1 = _col0 + 1

		_del_x = col / self.scale - _col0
		_del_y = row / self.scale - _row0

		# print col, row, _col0, _row0, self.mat.shape
		_mat_00x = self.mat[_row0][_col0][2]
		_mat_01x = self.mat[_row0][_col1][2]
		_mat_10x = self.mat[_row1][_col0][2]
		_mat_11x = self.mat[_row1][_col1][2]

		_pos_x0 = _mat_00x + _del_x * (_mat_01x - _mat_00x)
		_pos_x1 = _mat_10x + _del_x * (_mat_11x - _mat_10x)
		_x = _pos_x0 + (_pos_x1 - _pos_x0) * _del_y

		_mat_00y = self.mat[_row0][_col0][3]
		_mat_01y = self.mat[_row0][_col1][3]
		_mat_10y = self.mat[_row1][_col0][3]
		_mat_11y = self.mat[_row1][_col1][3]

		_pos_y0 = _mat_00y + _del_y * (_mat_10y - _mat_00y)
		_pos_y1 = _mat_01y + _del_y * (_mat_11y - _mat_01y)
		_y = _pos_y0 + (_pos_y1 - _pos_y0) * _del_x

		return _x, _y

class projected_extent:

	def __init__(self, proj_tar, ext):
		self.proj_tar = proj_tar

		_pt_min = geo_point(ext.minx, ext.miny, ext.proj).project_to(proj_tar)
		_pt_max = geo_point(ext.maxx, ext.maxy, ext.proj).project_to(proj_tar)
		_pt_top = geo_point(ext.minx, ext.maxy, ext.proj).project_to(proj_tar)
		_pt_bot = geo_point(ext.maxx, ext.miny, ext.proj).project_to(proj_tar)

		_x_top = (_pt_top.x - _pt_min.x) / abs(ext.maxy - ext.miny)
		_y_top = (_pt_top.y - _pt_min.y) / abs(ext.maxy - ext.miny)

		_x_bot = (_pt_bot.x - _pt_min.x) / abs(ext.maxx - ext.minx)
		_y_bot = (_pt_bot.y - _pt_min.y) / abs(ext.maxx - ext.minx)

		_dist_x = _pt_min.distance_to(_pt_bot) / (ext.maxx - ext.minx)
		_dist_y = _pt_min.distance_to(_pt_top) / (ext.maxy - ext.miny)

		self.matrix = [_pt_min.x, _x_bot, _x_top, _pt_min.y, _y_bot, _y_top]
		self.extent = ext
		self.pt_min = _pt_min
		self.pt_max = _pt_max
		self.pt_top = _pt_top
		self.pt_bot = _pt_bot
		self.scale_x = _dist_x
		self.scale_y = _dist_y

	def project_offset(self, x_offset, y_offset):
		return self.matrix[0] + self.matrix[1] * x_offset + self.matrix[2] * y_offset, self.matrix[3] + self.matrix[4] * x_offset + self.matrix[5] * y_offset

	def get_extent(self):
		_xs = [self.pt_min.x, self.pt_max.x, self.pt_top.x, self.pt_bot.x]
		_ys = [self.pt_min.y, self.pt_max.y, self.pt_top.y, self.pt_bot.y]

		return geo_extent(min(_xs), min(_ys), max(_xs), max(_ys), self.proj_tar)

class geo_point:
	@classmethod
	def from_raster(cls, raster, col, row):
		_x, _y = raster.to_location(col, row)
		return cls(_x, _y, raster.proj)

	def __init__(self, x, y, proj=None):
		self.x = x
		self.y = y
		self.proj = proj
		self.geom = None

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
		import geo_raster

		if self.band:
			return self.band

		logging.info('loading band file ' + self.file)
		_img = None
		if self.unzip and self.file.endswith('.gz'):
			_img = geo_raster.geo_raster.open(self.unzip.unzip(self.file))
		else:
			_img = geo_raster.geo_raster.open(self.file)

		if self.dataset_name:
			_img = _img.get_subdataset(self.dataset_name)

		self.band = _img.get_band(self.band_idx)
		return self.band

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
			self.band.clean()
			self.band = None

class geo_band_stack_zip:

	def __init__(self, bands, proj=None):
		if len(bands) == 0:
			raise Exception('the band array is empty')

		self.bands = bands
		_proj = proj
		for _b in bands:
			if _proj == None:
				_proj = _b.poly.proj

		self.last_band = None
		self.proj = _proj

	@classmethod
	def from_shapefile(cls, f_list, band_idx=1, dataset_name=None, file_unzip=None):
		from osgeo import ogr

		_bnds = []
		_shp = ogr.Open(f_list)
		_lyr = _shp.GetLayer()

		import os
		_d_shp = os.path.dirname(f_list)

		for _f in _lyr:
			_poly = geo_polygon(_f.geometry().Clone())
			_file = _f.items()['file']

			if _file[0] == '/' or _file[1] == ':':
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

		return cls(_bnds, _lyr.GetSpatialRef())

	def clean(self):
		for _b in self.bands:
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

	def get_band_xy(self, x, y):
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

	def read_xy(self, x, y, cache=True):
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
			if _v != None:
				self.last_band = i
				return _v

	def read(self, pt, cache=True):
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
			if _v != None:
				self.last_band = i
				return _v

	def get_bands(self, poly):
		_poly = poly.project_to(self.proj)

		_ls = []
		for i in xrange(len(self.bands)):
			if self.bands[i].poly.is_intersect(_poly):
				_ls.append(self.bands[i])

		return _ls

class geo_band_stack:

	def __init__(self, bands, proj=None):
		if len(bands) == 0:
			raise Exception('the band array is empty')

		self.bands = bands

		_proj = proj
		_exts = []
		for _b in bands:
			_exts.append(_b.poly)
			if _proj == None:
				_proj = _b.poly.proj

		self.pixel_type = bands[0].band.pixel_type
		self.nodata = bands[0].band.nodata
		self.cell_size = bands[0].raster.geo_transform[1]

		self.extents = _exts
		self.last_extent = None
		self.proj = _proj

	@classmethod
	def from_shapefile(cls, f_list, band=1):
		from osgeo import ogr

		_ls = []
		_shp = ogr.Open(f_list)
		_lyr = _shp.GetLayer()

		import os
		_d_shp = os.path.dirname(f_list)

		for _f in _lyr:
			_file = _f.items()['file']

			if _file[0] in ['/', '\\']:
				# handle relative path
				_file = _d_shp + os.sep + _file

			logging.debug('loading ' + _file)
			_ls.append(_file)

		return cls.from_list(_ls, band)

	@classmethod
	def from_file(cls, f, band=1):
		return cls.from_list(open(f).read().splitlines(), band)

	@classmethod
	def from_list(cls, ls, band=1):
		import geo_raster, os

		_bnds = []
		for _f in ls:
			# load band from the image
			if not os.path.exists(_f): continue

			if _f.endswith('.hdf'):
				# load band from sub dataset, such as HDF
				_bnd = geo_raster.geo_raster.open(_f).get_subdataset(band).get_band()
			else:
				_bnd = geo_raster.geo_raster.open(_f).get_band(band)
			_bnds.append(geo_band_reader(_bnd))

		return cls(_bnds)

	def clean(self):
		for _b in self.bands:
			_b.band.clean()

	def get_band(self, pt):
		if self.last_extent != None and self.extents[self.last_extent].is_contain(pt):
			return self.bands[self.last_extent]

		for i in xrange(len(self.extents)):
			if i == self.last_extent:
				continue

			if self.extents[i].is_contain(pt):
				self.last_extent = i
				return self.bands[i]

		return None

	def get_band_xy(self, x, y):
		_pt = geo_point(x, y)
		if self.last_extent != None and self.extents[self.last_extent].is_contain(_pt):
			return self.bands[self.last_extent]

		for i in xrange(len(self.extents)):
			if i == self.last_extent:
				continue

			if self.extents[i].is_contain(_pt):
				self.last_extent = i
				return self.bands[i]
		return None

	def read_xy(self, x, y, cache=True):
		_v = None
		if self.last_extent != None:
			_v = self.bands[self.last_extent].read(x, y, cache)
			if _v != None:
				return _v

		_pt = geo_point(x, y)
		for i in xrange(len(self.extents)):
			if i == self.last_extent:
				continue

			if not self.extents[i].is_contain(_pt):
				continue

			_v = self.bands[i].read(x, y, cache)
			if _v != None:
				self.last_extent = i
				return _v

	def read(self, pt, cache=True):
		_v = None
		if self.last_extent != None:
			_v = self.bands[self.last_extent].read_point(pt, cache)
			if _v != None:
				return _v

		for i in xrange(len(self.extents)):
			if i == self.last_extent:
				continue

			if not self.extents[i].is_contain(pt):
				continue

			_v = self.bands[i].read_point(pt, cache)
			if _v != None:
				self.last_extent = i
				return _v

class geo_band_reader:

	def __init__(self, band, name=None):
		self.name = name
		self.band = band
		self.raster = band.raster
		self.poly = geo_polygon.from_raster(self.raster)

	def read(self, x, y, cache=False):
		_val = self.band.read_location_cache(x, y) if cache else self.band.read_location(x, y)

		if _val == None or _val == self.band.nodata:
			return None

		return _val

	def read_point(self, pt, cache=False):
		_pt = pt.project_to(self.raster.projection_obj)
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
					if _v == None or _v == self.band.nodata:
						continue

					_vs.append(_v)

		return _v_o, max(_vs) - min(_vs)

def collect_samples(bnd_landsat, proj, interval=3000):
	_img_landsat = bnd_landsat.raster
	_read_landsat = geo_band_reader(bnd_landsat)

	_poly_union = geo_polygon.from_raster(_img_landsat).project_to(proj)
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

def process_images(f_landsat, nodata_landsat=None, interval=3000):
	import geo_raster

	_bnd_landsat = geo_raster.geo_raster.open(f_landsat).get_band()
	if nodata_landsat != None:
		_bnd_landsat.nodata = nodata_landsat

	return collect_samples(_bnd_landsat, modis_projection())

def write_samples(locs, f_output):
	print 'write', len(locs), 'samples'

	_ls = ['x,y']
	for _s in locs:
		_ls.append('%f,%f' % (_s.x, _s.y))

	open(f_output, 'w').write('\n'.join(_ls))

def read_samples(f_sample, proj=None):
	_vs = []
	for _l in open(f_sample).read().splitlines()[1:]:
		_ps = _l.split(',')
		if len(_ps) == 2:
			_vs.append(geo_point(float(_ps[0]), float(_ps[1]), proj))

	return _vs

