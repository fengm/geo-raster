
from osgeo import gdal, ogr, osr
import re

class band_info:

	def __init__(self, geo_transform, width, height, proj, nodata=None, pixel_type=None):
		self.geo_transform = geo_transform
		self.width = width
		self.height = height
		self.proj = proj
		self.nodata = nodata
		self.pixel_type = pixel_type

class geo_band_cache:

	def __init__(self, data, geo_transform, proj, nodata=None, pixel_type=None):
		self.width = data.shape[1]
		self.height = data.shape[0]
		self.geo_transform = geo_transform
		self.proj = proj
		self.nodata = nodata
		self.data = data
		self.pixel_type = pixel_type

	def read_location(self, x, y):
		'''Read a cell at given coordinate'''
		_col, _row = self.to_cell(x, y)
		if _col < 0 or _row < 0 or _col >= self.width or _row >= self.height:
			return None
		return self.data[_row, _col]

	def read_cell(self, col, row):
		'''Read a cell at given col/row'''
		if col < 0 or row < 0 or col >= self.width or row >= self.height:
			return None
		return self.data[row, col]

	def write_cell(self, col, row, val):
		if col < 0 or row < 0 or col >= self.width or row >= self.height:
			return
		self.data[row, col] = val

	def to_cell(self, x, y):
		return to_cell(self.geo_transform, x, y)

	def to_location(self, col, row):
		return to_location(self.geo_transform, col, row)

	def write(self, f):
		'''write the raster to file'''
		_pixel_type = self.pixel_type
		if _pixel_type == None:
			from osgeo import gdal
			_pixel_type = gdal.GDT_Byte
		write_raster(f, self.geo_transform, self.proj.ExportToWkt(), self.data, nodata=self.nodata, pixel_type=_pixel_type)

	def band_info(self):
		return band_info(self.geo_transform, self.width, self.height, self.proj, self.nodata, self.pixel_type)

class geo_band():
	'''A raster band'''

	def __init__(self, raster, band):
		self.raster = raster
		self.band = band
		self.description = band.GetDescription()
		self.names = band.GetRasterCategoryNames()
		self.width = band.XSize
		self.height = band.YSize
		self.size = [self.height, self.width]
		self.data = None
		self.buf_row_start = -1
		self.nodata = band.GetNoDataValue()
		self.pixel_type = band.DataType
		self.color_table = band.GetColorTable()
		self.geo_transform = raster.geo_transform
		self.proj = raster.projection_obj
		self.test = None

	def clean(self):
		'''clean cached data'''
		del self.data
		self.data = None
		self.buf_row_start = -1

	def read_location_cache(self, x, y):
		'''Read a cell at given coordinate. the entire band is cached to avoid multiple IO'''
		if self.data == None:
			self.read()

		_col, _row = self.raster.to_cell(x, y)
		if _col < 0 or _row < 0 or _col >= self.width or _row >= self.height:
			return None

		return self.data[_row, _col]

	def read_cell_cache(self, col, row):
		'''Read a cell at given col/row, the entire band is cached to avoid multiple IO'''
		if col < 0 or row < 0 or col >= self.width or row >= self.height:
			return None

		if self.data == None:
			self.read()

		return self.data[row, col]

	def read_location(self, x, y, row_num=6):
		'''Read a cell at given coordinate'''

		_col, _row = self.raster.to_cell(x, y)
		return self.read_cell(_col, _row, row_num)

	def to_cell(self, x, y):
		return to_cell(self.geo_transform, x, y)

	def to_location(self, col, row):
		return to_location(self.geo_transform, col, row)

	def is_cached(self, row):
		if not (0 <= row < self.height):
			return False

		if self.data== None or self.buf_row_start < 0 or not (self.buf_row_start <= row < self.buf_row_start + self.data.shape[0]):
			return False

		return True

	def read_cell(self, col, row, row_num=6):
		'''Read a cell at given col/row'''

		if col < 0 or row < 0 or col >= self.width or row >= self.height:
			return None

		if not self.is_cached(row):
			self.read_rows(row, row_num)

		return self.data[row - self.buf_row_start, col]

	def read_rows(self, row, row_num=6):
		'''Read rows from the raster band and cache them'''

		del self.data
		self.data = None

		_rows = row_num
		if row + _rows > self.height:
			_rows = self.height - row

		self.data = self.band.ReadAsArray(0, row, self.width, _rows, self.width, _rows)
		self.buf_row_start = row

		return self.data

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

	def band_info(self):
		_img = self.raster
		return band_info(_img.geo_transform, self.width, self.height,
				_img.projection_obj, self.nodata, self.pixel_type)

	def cache(self):
		_img = self.raster
		_dat = self.read_rows(0, self.height)
		return geo_band_cache(_dat, _img.geo_transform, _img.proj,
				self.nodata, self.pixel_type)

class geo_raster():
	def __init__(self, f, raster):
		self.filepath = f
		self.raster = raster
		if not self.raster:
			raise Exception('failed to load file "%s"' % f)
		self.init_vars()

	@classmethod
	def open(cls, f, update=False):
		if update:
			return cls(f, gdal.Open(f, gdal.GA_Update))

		return cls(f, gdal.Open(f))

	@classmethod
	def create(cls, f, size, geo_transform, proj, pixel_type=gdal.GDT_Byte, driver='GTiff', nodata=None, color_table=None):
		if f.lower().endswith('.img'):
			driver = 'HFA'

		_driver = gdal.GetDriverByName(driver)
		_size = len(size) == 2 and [1] + size or size

		_img = _driver.Create(f, _size[2], _size[1], _size[0], pixel_type)
		for _b in xrange(_size[0]):
			_band = _img.GetRasterBand(_b + 1)

			if nodata != None:
				_band.SetNoDataValue(nodata)
			if color_table != None:
				_band.SetColorTable(color_table)

		_img.SetGeoTransform(geo_transform)
		proj and _img.SetProjection(proj)

		return cls(f, _img)

	def sub_datasets(self):
		return self.raster.GetSubDatasets()

	def get_subdataset(self, band):
		_band = str(band)
		for _n, _d in self.raster.GetSubDatasets():
			if _n.endswith(_band):
				return geo_raster.open(_n.strip())

		return None

	def init_vars(self):
		self.geo_transform = self.raster.GetGeoTransform()
		self.band_num = self.raster.RasterCount
		self.width = self.raster.RasterXSize
		self.projection = self.raster.GetProjection()
		self.height = self.raster.RasterYSize
		self.size = [self.band_num, self.height, self.width]
		self.cell_size_x = self.geo_transform[1]
		self.cell_size_y = self.geo_transform[5]
		self.cell_size = self.cell_size_x
		self.projection_obj = osr.SpatialReference()
		self.projection_obj.ImportFromWkt(self.projection)
		# compatiable with the geo_band_cache
		self.proj = self.projection_obj

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

	def save(self, fou):
		if fou.lower().endswith('.img'):
			driver = 'HFA'

		_bnd = self.get_band(1)
		_driver = gdal.GetDriverByName(driver)

		_img = _driver.Create(fou, self.width,
				self.height, self.band_num, _bnd.pixel_type)

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

def write_raster(f, geo_transform, proj, img, pixel_type=gdal.GDT_Byte, driver='GTiff', nodata=None, color_table=None):
	if f.lower().endswith('.img'):
		driver = 'HFA'

	_driver = gdal.GetDriverByName(driver)

	_size = img.shape
	if len(_size) == 2:
		_img = _driver.Create(f, _size[1], _size[0], 1, pixel_type)

		_band = _img.GetRasterBand(1)
		if color_table != None:
			_band.SetColorTable(color_table)
		if nodata != None:
			_band.SetNoDataValue(nodata)
		_band.WriteArray(img)
		_band.FlushCache()
	else:
		_img = _driver.Create(f, _size[2], _size[1], _size[0], pixel_type)
		for _b in xrange(_size[0]):
			_band = _img.GetRasterBand(_b + 1)

			if nodata != None:
				_band.SetNoDataValue(nodata)
			if color_table != None:
				_band.SetColorTable(color_table)
			_band.WriteArray(img[_b, :, :])
			_band.FlushCache()

	_img.SetGeoTransform(geo_transform)
	proj and _img.SetProjection(proj)

def map_colortable(cs):
	_color_tables = gdal.ColorTable()
	for i in xrange(256):
		if i in cs:
			_color_tables.SetColorEntry(i, cs[i])

	return _color_tables

def load_colortable(f):
	_colors = {}
	for _l in open(f).read().splitlines():
		_vs = re.split('\s+', _l)
		if len(_vs) != 2:
			print 'ignore', _l
			continue

		_colors[float(_vs[0])] = tuple([int(_v) for _v in _vs[1].split(',')])

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

