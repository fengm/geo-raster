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
import os
import logging

import numpy
cimport numpy as np
cimport cython

import math
from . import geo_base as gb
from . import file_unzip
from . import run_commands
from . import file_mag
from . import config
from . import color_table

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
    return math.floor((val - ref) / div) * div + ref

cdef align_max(val, ref, div):
    return math.ceil((val - ref) / div) * div + ref
    

def default_geotiff_opts():
    return ['predictor=2', 'tiled=yes', 'compress=lzw']
    
def is_same_projs(proj1, proj2):
    if None is [proj1, proj2]:
        return True

    if proj1.ExportToProj4() == proj2.ExportToProj4():
        return True

    if proj1.IsSame(proj2):
        return True

    return False

class geo_raster_info:
    def __init__(self, geo_transform, width, height, proj):
        self.geo_transform = geo_transform
        self.width = width
        self.height = height
        self.proj = proj
        self.cell_size = self.geo_transform[1]

    def __del__(self):
        self.geo_transform = None
        self.width = None
        self.height = None
        self._proj = None

    @property
    def proj(self):
        return gb.proj_from_wkt(self._proj)
    
    @proj.setter
    def proj(self, val):
        if not val:
            self._proj = None
        else:
            self._proj = val.ExportToWkt()
    
    def to_cell(self, float x, float y):
        return to_cell(self.geo_transform, x, y)

    def to_location(self, int col, int row):
        return to_location(self.geo_transform, col, row)

    def extent(self):
        _geo = self.geo_transform

        _pt1 = (_geo[0], _geo[3])
        _pt2 = (_geo[0] + self.width * _geo[1] + self.height * _geo[2], \
                _geo[3] + self.width * _geo[4] + self.height * _geo[5])

        return gb.geo_extent(_pt1[0], _pt2[1], _pt2[0], _pt1[1], self.proj)

    def cell_extent(self, col, row):
        _trans = self.geo_transform

        _cell_x = _trans[1] / 2
        _cell_y = _trans[5] / 2

        _pt0 = self.to_location(col, row)

        return gb.geo_extent(_pt0[0] - _cell_x, _pt0[1] - _cell_y,
                _pt0[0] + _cell_x, _pt0[1] + _cell_y, self.proj)

    def scale(self, ratio=None, ceil=False, cell_size=None):
        _geo = list(self.geo_transform)

        _r = ratio
        if cell_size is not None:
            _r = _geo[1] / cell_size

        if _r is None:
            raise Exception('no valid param provided')

        _cols = int(math.ceil(self.width * _r) if ceil else math.floor(self.width * _r))
        _rows = int(math.ceil(self.height * _r) if ceil else math.floor(self.height * _r))

        _geo[1] /= _r
        _geo[2] /= _r
        _geo[4] /= _r
        _geo[5] /= _r

        return geo_raster_info(tuple(_geo), _cols, _rows, self.proj)

    def subset(self, col, row, width, height):
        _geo = list(self.geo_transform)

        _geo[0] += col * _geo[1] + row * _geo[2]
        _geo[3] += col * _geo[4] + row * _geo[5]

        _cols = min(width, self.width - col)
        _rows = min(height, self.height - row)

        if _cols <= 0 or _rows <= 0:
            logging.warning('out of the band extent')
            return None

        return geo_raster_info(_geo, _cols, _rows, self.proj)

    def from_ma_grid(self, grid, update_type=True, nodata=None):
        _nodata = nodata
        if _nodata is None:
            _nodata = self.nodata

        if _nodata is None:
            raise Exception('nodata is required')

        _dat = grid.filled(_nodata)
        return self.from_grid(_dat, update_type, _nodata)

    def from_grid(self, grid, update_type=True, nodata=None):
        if not (self.height == grid.shape[-2] and self.width == grid.shape[-1]):
            raise Exception('grid size does not match')

        _nodata = nodata
        if _nodata is None:
            _nodata = self.nodata

        _dat = grid

        return geo_band_cache(_dat, list(self.geo_transform), self.proj, _nodata, gb.from_dtype(grid.dtype))

class geo_band_info(geo_raster_info):

    def __init__(self, geo_transform, width, height, proj, nodata=None, pixel_type=None):
        geo_raster_info.__init__(self, geo_transform, width, height, proj)
            
        self.pixel_type = pixel_type
        self.nodata = self.est_nodata(nodata)

    def __del__(self):
        try:
            super().__del__()
        except AttributeError:
            pass

        self.pixel_type = None
        self.nodata = None

    def get_nodata(self, nodata=None):
        return self.nodata
        
    def est_nodata(self, nodata=None):
        _nodata = nodata
        
        if nodata is not None:
            # reset the nodata to address the incorrect nodata when nodata set
            if self.pixel_type < 3 and _nodata <= -32767.0:
                _nodata = None
                
        if self.pixel_type is None:
            return _nodata
            
        if _nodata is None:
            _default_nodata = {1: 255, 2: 65535, 3: -9999, 4: (2 ** 32) - 1, 5: -9999, 6: -9999, 7: -9999}
            if self.pixel_type not in _default_nodata.keys():
                raise Exception('Unsupport data type %s' % self.pixel_type)

            _nodata = _default_nodata[self.pixel_type]
            logging.debug('No nodata value provided, using default value (%s)' % _nodata)

        return _nodata

    def subset(self, col, row, width, height):
        _geo = list(self.geo_transform)

        _geo[0] += col * _geo[1] + row * _geo[2]
        _geo[3] += col * _geo[4] + row * _geo[5]

        _cols = min(width, self.width - col)
        _rows = min(height, self.height - row)

        if _cols <= 0 or _rows <= 0:
            logging.warning('out of the band extent')
            return None

        return geo_band_info(_geo, _cols, _rows, self.proj, self.nodata, self.pixel_type)

    def sub_band(self, col, row, width, height):
        return self.subset(col, row, width, height)

    def align(self, ext, clip=False):
        _geo = self.geo_transform

        _cell = _geo[1]

        _s_x = _geo[0]
        # if _s_x > ext.minx:
        #    _s_x -= (int((_s_x - ext.minx) / _cell) + 10)  * _cell

        _s_y = _geo[3]
        # if _s_y < ext.maxy:
        #    _s_y += (int((ext.maxy - _s_y) / _cell) + 10)  * _cell

        _min_x = align_min(ext.minx, _s_x, _cell)
        _max_x = align_max(ext.maxx, _s_x, _cell)

        _min_y = align_min(ext.miny, _s_y, _cell)
        _max_y = align_max(ext.maxy, _s_y, _cell)

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

        return geo_band_info([_min_x, _cell, 0, _max_y, 0, _cell * -1], _cols, _rows, self.proj, \
                self.nodata, self.pixel_type)

    def scale(self, ratio=None, ceil=False, cell_size=None):
        _geo = list(self.geo_transform)

        _r = ratio
        if cell_size is not None:
            _r = _geo[1] / cell_size

        if _r is None:
            raise Exception('no valid param provided')

        _cols = int(math.ceil(self.width * _r) if ceil else math.floor(self.width * _r))
        _rows = int(math.ceil(self.height * _r) if ceil else math.floor(self.height * _r))

        _geo[1] /= _r
        _geo[2] /= _r
        _geo[4] /= _r
        _geo[5] /= _r

        return geo_band_info(tuple(_geo), _cols, _rows, self.proj, self.nodata, self.pixel_type)

class geo_band_cache(geo_band_info):

    def __init__(self, data, geo_transform, proj, nodata=None, pixel_type=None, color_table=None):
        geo_band_info.__init__(self, geo_transform, data.shape[-1], data.shape[-2], proj, nodata, pixel_type)
        self.data = data
        self.color_table = color_table

    def __del__(self):
        try:
            super().__del__()
        except AttributeError:
            pass
        
        self.data = None

    @property
    def data_ma(self):
        if None == self.nodata:
            raise Exception('nodata is required')
        return numpy.ma.masked_equal(self.data, self.nodata)

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

        if self.data.dtype == numpy.int8:
            return read_pixel_byte(self.data, row, col)
        elif self.data.dtype == numpy.uint8:
            return read_pixel_ubyte(self.data, row, col)
        elif self.data.dtype == numpy.uint16:
            return read_pixel_uint16(self.data, row, col)
        elif self.data.dtype == numpy.int16:
            return read_pixel_int16(self.data, row, col)
        elif self.data.dtype == numpy.uint32:
            return read_pixel_uint32(self.data, row, col)
        elif self.data.dtype == numpy.int32:
            return read_pixel_int32(self.data, row, col)
        elif self.data.dtype == numpy.float32:
            return read_pixel_float32(self.data, row, col)
        else:
            return self.data[row][col]

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
        if _pixel_type is None:
            _pixel_type = gdal.GDT_Byte
        write_raster(f, self.geo_transform, self.proj.ExportToWkt(),
                self.data, nodata=self.nodata, pixel_type=_pixel_type, opts=opts)

    def save(self, f, driver='GTiff', color_table=None, opts=[]):
        '''write the raster to file'''
        _pixel_type = self.pixel_type
        if _pixel_type is None:
            _pixel_type = gdal.GDT_Byte
            
        _color_table = color_table if color_table else self.color_table
        write_raster(f, self.geo_transform, self.proj.ExportToWkt(), \
                self.data, nodata=self.nodata, pixel_type=_pixel_type, \
                driver=driver, color_table=_color_table, opts=opts)

    def read_ext(self, ext, roundup=True, check_proj=True):
        if ext is None:
            return None

        if check_proj and not is_same_projs(ext.proj, self.proj):
            logging.info('proj1: %s' % self.proj.ExportToProj4() if self.proj else None)
            logging.info('proj2: %s' % ext.proj.ExportToProj4() if ext.proj else None)

            raise Exception('The extent is supposed to be in the same CRS as the band does')

        _ext1 = self.extent()
        if _ext1.minx == ext.minx and _ext1.maxy == ext.maxy \
            and _ext1.maxx == ext.maxx and _ext1.miny == ext.miny:
            # if the band has same size and extent then return without
            # adjustment
            return self

        _geo1 = list(self.geo_transform)
        _cell = _geo1[1]
        _fill = self.get_nodata()

        if roundup:
            _cols = int(round((ext.width() / _cell)))
            _rows = int(round((ext.height() / _cell)))
        else:
            _cols = int(math.ceil((ext.width() / _cell)))
            _rows = int(math.ceil((ext.height() / _cell)))

        _dat = numpy.empty((_rows, _cols), dtype=self.data.dtype)
        _dat.fill(_fill)

        _ext = gb.geo_extent.from_raster(self).intersect(ext)

        if roundup:
            _off_x1 = int(round((_ext.minx - _geo1[0]) / _cell))
            _off_y1 = int(round((_geo1[3] - _ext.maxy) / _cell))

            _off_x2 = int(round((_ext.minx - ext.minx) / _cell))
            _off_y2 = int(round((ext.maxy - _ext.maxy) / _cell))
        else:
            _off_x1 = int((_ext.minx - _geo1[0]) / _cell)
            _off_y1 = int((_geo1[3] - _ext.maxy) / _cell)

            _off_x2 = int((_ext.minx - ext.minx) / _cell)
            _off_y2 = int((ext.maxy - _ext.maxy) / _cell)

        _w = min(_cols, int(math.ceil((_ext.width() / _cell))))
        _h = min(_rows, int(math.ceil((_ext.height() / _cell))))

        _dat[_off_y2: _off_y2 + _h, _off_x2: _off_x2 + _w] = \
                self.data[_off_y1: _off_y1 + _h, _off_x1: _off_x1 + _w]

        _geo2 = list(_geo1)

        _geo2[0] = _ext.minx
        _geo2[3] = _ext.maxy

        return geo_band_cache(_dat, _geo2, self.proj, _fill,
                self.pixel_type, self.color_table)

    def read_block(self, bnd, check_proj=True, apply_nni=True):
        if bnd is None:
            return None

        if apply_nni and (bnd.geo_transform[1] == self.geo_transform[1]) and is_same_projs(bnd.proj, self.proj):
            logging.debug('reading from ext')
            _bnd = self.read_ext(bnd.extent(), True, False)
            if _bnd:
                assert(_bnd.width == bnd.width and _bnd.height == bnd.height)
            return _bnd

        _prj = gb.projection_transform.from_band(bnd, self.proj)

        _pol_t1 = gb.geo_polygon.from_raster(bnd).segment_ratio(10)
        _pol_t2 = _pol_t1.project_to(self.proj)
        if _pol_t2 is None:
            return None

        _bnd = self
        _pol_s = gb.geo_polygon.from_raster(_bnd).segment_ratio(10)

        # calculate the intersection area for both data sets
        _pol_c_s = _pol_s.intersect(_pol_t2)
        if _pol_c_s is None or _pol_c_s.poly is None:
            logging.debug('The raster does not cover the request bnd')
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

        _ext_s_cs = gb.geo_extent(_col_s_s, _row_s_s,
                _col_s_e, _row_s_e)

        _row_s_s = 0
        _dat = _bnd.data
        if _dat is None:
            return None

        _col_t_s, _row_t_s = to_cell(tuple(bnd.geo_transform),
                _ext_t.minx, _ext_t.maxy)
        _col_t_e, _row_t_e = to_cell(tuple(bnd.geo_transform),
                _ext_t.maxx, _ext_t.miny)

        _ext_t_cs = gb.geo_extent(_col_t_s, _row_t_s,
                _col_t_e, _row_t_e)

        _nodata = self.get_nodata()
        _dat_out = numpy.empty([bnd.height, bnd.width],
                dtype=gb.to_dtype(self.pixel_type))
        _dat_out.fill(_nodata)
        
        if isinstance(_bnd.geo_transform, list):
            _bnd.geo_transform = tuple(_bnd.geo_transform)

        if self.pixel_type == 1:
            gb.read_block_uint8(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 2:
            gb.read_block_uint16(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 3:
            gb.read_block_int16(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 4:
            gb.read_block_uint32(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 5:
            gb.read_block_int32(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 6:
            gb.read_block_float32(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 7:
            gb.read_block_float64(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        else:
            raise Exception('The pixel type is not supported ' + \
                    str(self.pixel_type))

        return geo_band_cache(_dat_out, bnd.geo_transform, bnd.proj,
                _nodata, self.pixel_type, self.color_table)
    
    def mask(self, f):
        with file_unzip.zip() as _zip:
            _f_out = _zip.generate_file('', '.tif')
            
            bnd = self
            
            _dat = numpy.zeros((bnd.height, bnd.width), dtype=numpy.uint8)
            _bnd = bnd.from_grid(_dat)
            _bnd.pixel_type = pixel_type()
            _bnd.save(_f_out)
            
            _f_inp = file_mag.get(f).get()
            _f_shp = _f_inp
        
            _shp = ogr.Open(_f_inp)
            _lyr = _shp.GetLayer()
        
            if not _lyr.GetSpatialRef().IsSame(_bnd.proj):
                _f_shp = _zip.generate_file('', '.shp')
        
                _cmd = 'ogr2ogr -t_srs "%s" %s %s' % (_bnd.proj.ExportToProj4(), _f_shp, _f_inp)
                run_commands.run(_cmd)
        
            _cmd = 'gdal_rasterize -at -burn 1 %s %s' % (_f_shp, _f_out)
            run_commands.run(_cmd)
            
            _bbb = geo_raster.open(_f_out).get_band().cache()
            bnd.data[_bbb.data != 1] = bnd.nodata
            
    def colorize_byte(self, f=None, interpolate=False):
        cdef np.ndarray[np.uint8_t, ndim=2] _dat = numpy.empty((self.height, self.width), dtype=numpy.uint8)
        _dat.fill(255)
        
        _ms = color_table.color_mapping(color_table.color_table(self.color_table if f is None else f), interpolate=interpolate)
        _ks = sorted(_ms._values.keys())
        
        _idx = self.data != (self.nodata if self.nodata is not None else -9999)
        for _k in _ks:
            _i = _idx & (self.data >= _k)
            _dat[_i] = _ms.get_code(_k)
            _idx = _i
            
        _out = self.from_grid(_dat, nodata=255)
        _out.color_table = _ms._colors.ogr_color_table()
        
        return _out
        
    def colorize_rgba(self, f=None, interpolate=True):
        _dat = numpy.empty((4, self.height, self.width), dtype=numpy.uint8)
        _dat.fill(0)
        
        _ms = color_table.color_mapping(color_table.color_table(self.color_table if f is None else f), interpolate=interpolate)
        _ks = sorted(_ms._values.keys())
        
        if numpy.isnan(self.nodata):
            _idx = numpy.logical_not(numpy.isnan(self.data))
        else:
            _idx = (self.data != (self.nodata if self.nodata is not None else -9999))
        # _idx = numpy.logical_not(numpy.isnan(self.data)) & (self.data != (self.nodata if self.nodata is not None else -9999))

        for _k in _ks:
            _c = _ms.get_color(_k)
            
            _i = numpy.greater_equal(self.data, _k, where=_idx) & _idx
            for _b in range(4):
                _dat[_b, :, :][_i] = _c[_b]
                
            _idx = _i
            
        _out = self.from_grid(_dat)
        return _out
        
    def to_image(self):
        if len(self.data.shape) != 3:
            raise Exception('only support 3 dementions array')
            
        from PIL import Image
        _dat = numpy.transpose(self.data, [1, 2, 0])
        return Image.fromarray(_dat, 'RGBA')
        
class geo_band(geo_band_info):
    '''A raster band'''

    def __init__(self, raster, band, convert_list=False):
        geo_band_info.__init__(self, raster.geo_transform, band.XSize, band.YSize,
                raster.proj, band.GetNoDataValue(), band.DataType)

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

        _clr = band.GetColorTable()
        if _clr is None:
            self.color_table = None
        else:
            self.color_table = _clr.Clone()
        del _clr

        self.test = None
        self.convert_list = convert_list

    def __del__(self):
        try:
            super().__del__()
        except AttributeError:
            pass
        
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
        if self.data is None:
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

        if self.data is None:
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

        if self.data is None or self.buf_row_start < 0 or not \
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

        if _s == 2 or self.data is None:
            self.read_rows(max(0, row - row_num / 3), row_num)

        if self.data is None:
            return None

        cdef int _row = row - self.buf_row_start
        if self.pixel_type == 1:
            if self.data.dtype == numpy.int8:
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

        if _cols <= 0 or _rows <= 0 or row < 0:
            return None

        _d = self.band.ReadAsArray(col, row, _cols, _rows, _cols, _rows)
        if _d is None:
            return None

        self.data = _d
        self.buf_row_start = row
        self.buf_row_end = row + _d.shape[0]
        self.buf_col_start = col
        self.buf_col_end = col + _d.shape[1]

        return self.data

    def read_grid(self, col, row, width, height):
        _dat = self.read_rows(row, height, col, width)
        if _dat is None:
            raise Exception('failed to read block')

        _geo = list(self.geo_transform)

        _geo[0] += col * _geo[1] + row * _geo[2]
        _geo[3] += col * _geo[4] + row * _geo[5]

        _rows = _dat.shape[0]
        _cols = _dat.shape[1]

        if _cols <= 0 or _rows <= 0:
            raise Exception('out of the band extent')

        return geo_band_cache(_dat, _geo, self.proj, self.nodata, self.pixel_type, self.color_table)

    @property
    def cached(self):
        _dat = self.data
        if type(_dat) == type(None):
            return None

        _geo = list(self.geo_transform)

        _col = self.buf_col_start
        _row = self.buf_row_start

        _geo[0] += _col * _geo[1] + _row * _geo[2]
        _geo[3] += _col * _geo[4] + _row * _geo[5]

        return geo_band_cache(_dat, _geo, self.proj, self.nodata, self.pixel_type, self.color_table)

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
                self.nodata, self.pixel_type, self.color_table)

    def read_ext(self, ext, roundup=True, check_proj=True):
        if ext is None:
            return None

        if check_proj and not is_same_projs(ext.proj, self.proj):
            logging.info('proj1: %s' % self.proj.ExportToProj4() if self.proj else None)
            logging.info('proj2: %s' % ext.proj.ExportToProj4() if ext.proj else None)

            raise Exception('The extent is supposed to be in the same CRS as the band does')

        _ext1 = self.extent()
        if _ext1.minx == ext.minx and _ext1.maxy == ext.maxy \
                and _ext1.maxx == ext.maxx and _ext1.miny == ext.miny:
            # if the band has same size and extent then return without
            # adjustment
            return self.cache()

        _geo1 = list(self.geo_transform)
        _cell = _geo1[1]
        _fill = self.get_nodata()

        if roundup:
            _cols = int(round((ext.width() / _cell)))
            _rows = int(round((ext.height() / _cell)))
        else:
            _cols = int(math.ceil((ext.width() / _cell)))
            _rows = int(math.ceil((ext.height() / _cell)))

        if _cols == 0 or _rows == 0:
            return None

        _dat = numpy.empty((_rows, _cols), dtype=gb.to_dtype(self.pixel_type))
        _dat.fill(_fill)

        _ext = gb.geo_extent.from_raster(self).intersect(ext)

        if roundup:
            _off_x1 = int(round((_ext.minx - _geo1[0]) / _cell))
            _off_y1 = int(round((_geo1[3] - _ext.maxy) / _cell))

            _off_x2 = int(round((_ext.minx - ext.minx) / _cell))
            _off_y2 = int(round((ext.maxy - _ext.maxy) / _cell))
        else:
            _off_x1 = int((_ext.minx - _geo1[0]) / _cell)
            _off_y1 = int((_geo1[3] - _ext.maxy) / _cell)

            _off_x2 = int((_ext.minx - ext.minx) / _cell)
            _off_y2 = int((ext.maxy - _ext.maxy) / _cell)

        _w = int(math.ceil((_ext.width() / _cell)))
        _h = int(math.ceil((_ext.height() / _cell)))
        _w = min(_w, self.width - _off_x1, _cols)
        _h = min(_h, self.height - _off_y1, _rows)

        if _w <= 0 or _h <= 0:
            logging.info('the target array is too small (%s, %s)' % (_w, _h))
            return None

        _ddd = self.read_rows(_off_y1, _h)
        if _ddd is None:
            logging.info('failed to return array for the target')
            return None

        if _ddd.shape[0] <= 0 or _ddd.shape[1] <= 0:
            logging.info('the returned array is too small (%s, %s)' % (_w, _h))
            return None

        if _off_y2 + _h > _dat.shape[0]:
            return None

        if _off_x2 + _w > _dat.shape[1]:
            return None

        _dat[_off_y2: _off_y2 + _h, _off_x2: _off_x2 + _w] = _ddd[0: _h, _off_x1: _off_x1 + _w]

        _geo2 = list(_geo1)

        _geo2[0] = _ext.minx
        _geo2[3] = _ext.maxy

        return geo_band_cache(_dat, _geo2, self.proj, _fill,
                self.pixel_type, self.color_table)

    def read_block(self, bnd, check_proj=True, apply_nni=True):
        if bnd is None:
            return None

        if apply_nni and (bnd.geo_transform[1] == self.geo_transform[1]) and is_same_projs(bnd.proj, self.proj):
            _bnd = self.read_ext(bnd.extent(), True, check_proj)

            if _bnd:
                assert(_bnd.width == bnd.width and _bnd.height == bnd.height)
                return _bnd

        _prj = gb.projection_transform.from_band(bnd, self.proj)

        _pol_t1 = gb.geo_polygon.from_raster(bnd).segment_ratio(10)
        _pol_t2 = _pol_t1.project_to(self.proj)
        if _pol_t2 is None:
            # raise Exception('failed to project the grid extent')
            # skip the error and return None
            logging.debug('failed to project the grid extent')
            return None

        _bnd = self
        _pol_s = gb.geo_polygon.from_raster(_bnd).segment_ratio(10)

        # calculate the intersection area for both data sets
        _pol_c_s = _pol_s.intersect(_pol_t2)
        if _pol_c_s is None or _pol_c_s.poly is None:
            logging.debug('The raster does not cover the request bnd')
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

        _ext_s_cs = gb.geo_extent(_col_s_s, _row_s_s,
                _col_s_e, _row_s_e)

        # only load the intersection area to reduce memory use
        _row_s_s = max(0, _row_s_s - 1)
        _row_num = min(_row_s_e + 2, _bnd.height) - _row_s_s
        if _row_num <= 0:
            logging.debug('The raster does not cover the request bnd')
            return None

        _dat = _bnd.read_rows(_row_s_s, _row_num)

        _col_t_s, _row_t_s = to_cell(tuple(bnd.geo_transform),
                _ext_t.minx, _ext_t.maxy)
        _col_t_e, _row_t_e = to_cell(tuple(bnd.geo_transform),
                _ext_t.maxx, _ext_t.miny)

        _ext_t_cs = gb.geo_extent(_col_t_s, _row_t_s,
                _col_t_e, _row_t_e)

        _nodata = self.get_nodata()
        _dat_out = numpy.empty([bnd.height, bnd.width],
                dtype=gb.to_dtype(self.pixel_type))
        _dat_out.fill(_nodata)

        if self.pixel_type == 1:
            gb.read_block_uint8(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 2:
            gb.read_block_uint16(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 3:
            gb.read_block_int16(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 4:
            gb.read_block_uint32(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 5:
            gb.read_block_int32(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 6:
            gb.read_block_float32(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        elif self.pixel_type == 7:
            gb.read_block_float64(_dat, _ext_t_cs, _prj,
                    _bnd.geo_transform, _nodata, _row_s_s, _dat_out)
        else:
            raise Exception('The pixel type is not supported ' + \
                    str(self.pixel_type))

        return geo_band_cache(_dat_out, bnd.geo_transform, bnd.proj,
                _nodata, self.pixel_type, self.color_table)

class geo_raster(geo_raster_info):

    def __init__(self, f, raster):
        if not raster:
            raise Exception('failed to load raster')

        self.projection = raster.GetProjection()
        if not self.projection:
            _proj = None 
            self.projection = None
        else:
            _proj = osr.SpatialReference()
            _proj.ImportFromWkt(self.projection)

        _cols = raster.RasterXSize
        _rows = raster.RasterYSize

        geo_raster_info.__init__(self, raster.GetGeoTransform(), _cols, _rows, _proj)

        # self.projection_obj = _proj
        self.filepath = f
        self.raster = raster

        self.init_vars()

        _proj = None
        _cols = None
        _rows = None

    def __del__(self):
        geo_raster_info.__del__(self)

        self.projection = None
        # self.projection_obj = None
        self.filepath = None
        self.raster = None
        self.band_num = None
        self.size = None
        self.cell_size_x = None
        self.cell_size_y = None
        self.cell_size = None

    @property
    def projection_obj(self):
        return self.proj

    @staticmethod
    def _open_raster_file(f, update=False, iteration=0):
        if update:
            _img = gdal.Open(f, gdal.GA_Update)
        else:
            _img = gdal.Open(f)
            
        # retry another time for CEG
        if _img is None and f.startswith('/vsi') and iteration < 1:
            _f = file_mag.get(f)
            if _f is None or not _f.exists():
                return None
                
            # wait for 1.5 sec before retrying
            import time
            time.sleep(1.5)
            
            return geo_raster._open_raster_file(f, update, iteration+1)
            
        return _img
        
    @staticmethod
    def _load_s3_file(f):
        _m = re.match(r's3://([^/]+)/(.+)', f)
        if _m is None:
            raise Exception('failed to parse S3 file %s' % f)

        # if not _f.exists():
        #     logging.warning('%s does not exist' % f)
        #     return None
            
        _cache = config.getboolean('conf', 'cache_s3_image', False)
        
        if not _cache:
            _bucket = _m.group(1)
            _path = _m.group(2)

            _f = '/vsis3/%s/%s' % (_bucket, _path)
            return _f

        _f = file_mag.get(f)
        if not _f:
            return None
            
        return _f.get()
        
        # from gio import cache_mag
        # _s3 = cache_mag.s3(_bucket)

        # logging.debug('loading image from %s at %s' % (_bucket, _path))
        # return _s3, _s3.get(_path)

    @staticmethod
    def open(f, update=False, check_exist=True):
        if not f:
            logging.warning('requested for empty path')
            return None
            
        _f = f
        
        if _f.startswith('s3://'):
            _sf = geo_raster._load_s3_file(_f)
            if _sf is None:
                # logging.warning('invalid file name provided (%s)' % _f)
                return None
                
            _f = _sf
        else:
            if not _f.startswith('/vsi') and (check_exist and (not os.path.exists(_f))):
                logging.warning('failed to find the image %s' % f)
                return None

        _img = geo_raster._open_raster_file(_f, update)

        if _img is None:
            raise Exception('failed to load file ' + f)

        return geo_raster(f, _img)

    @staticmethod
    def create(f, size, geo_transform, proj, pixel_type=gdal.GDT_Byte, driver='GTiff', \
            nodata=None, color_table=None, opts=[]):

        if f.lower().endswith('.img'):
            driver = 'HFA'

        _driver = gdal.GetDriverByName(driver)
        _size = [1] + size if len(size) == 2 else size

        _img = _driver.Create(f, _size[2], _size[1], _size[0], pixel_type, opts)
        if _img is None:
            return None
        
        for _b in xrange(_size[0]):
            _band = _img.GetRasterBand(_b + 1)

            if nodata is not None:
                _band.SetNoDataValue(nodata)
            if color_table is not None:
                _band.SetColorTable(color_table)

        _img.SetGeoTransform(geo_transform)

        _prj = proj
        if _prj is None:
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
                return geo_raster.open(_n.strip(), check_exist=False)

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
            raise Exception('band index is not availible (bands %d/%d)' % (band_num, self.band_num))

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

            if _bnd_inp.nodata is not None:
                _bnd_out.SetNoDataValue(_bnd_inp.nodata)
            if _bnd_inp.color_table is not None:
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
        _pt.AssignSpatialReference(self.proj)
        _pt.TransformTo(proj)
        _pt = _pt.GetPoint_2D()

        return _pt

    def project_from(self, proj, x, y):
        _pt = ogr.Geometry(ogr.wkbPoint)

        _pt.SetPoint_2D(0, x, y)
        _pt.AssignSpatialReference(proj)
        _pt.TransformTo(self.proj)
        _pt = _pt.GetPoint_2D()

        return _pt

    def flush(self):
        """Flush the cache for writting"""
        self.raster.FlushCache()

def open(f, update=False):
    return geo_raster.open(f, update, True)

def write_raster(f, geo_transform, proj, img, pixel_type=gdal.GDT_Byte, driver='GTiff', nodata=None, color_table=None, opts=[]):
    if f.lower().endswith('.img'):
        driver = 'HFA'
        
    _opts = [] if opts is None else opts
    if driver == 'GTiff' and len(opts) == 0:
        _opts = default_geotiff_opts()

    _driver = gdal.GetDriverByName(driver)

    _size = img.shape
    if len(_size) == 2:
        _img = _driver.Create(f, _size[1], _size[0], 1, pixel_type, _opts)

        _band = _img.GetRasterBand(1)
        if color_table is not None:
            _band.SetColorTable(color_table)
        if nodata is not None:
            _band.SetNoDataValue(nodata)
        _band.WriteArray(img)
        _band.FlushCache()
    else:
        _img = _driver.Create(f, _size[2], _size[1], _size[0], pixel_type, _opts)
        for _b in xrange(_size[0]):
            _band = _img.GetRasterBand(_b + 1)

            if nodata is not None:
                _band.SetNoDataValue(nodata)
            if color_table is not None:
                _band.SetColorTable(color_table)
            _band.WriteArray(img[_b, :, :])
            _band.FlushCache()

    _img.SetGeoTransform(geo_transform)

    _prj = proj
    if _prj is None:
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
    import builtins

    _header = True
    _colors = {}

    for _l in builtins.open(f).read().splitlines():
        _l = _l.strip()
        if not _l:
            continue

        if _header:
            if _l.startswith('# QGIS'):
                return color_table.load(f)
            _header = False

        _vs = re.split('\s+', _l, maxsplit=1)
        if len(_vs) != 2:
            logging.warning('ignore color entry: %s' % _l)
            continue

        _cs = tuple([int(_v) for _v in re.split('\W+', _vs[1])])
        if len(_cs) < 3:
            raise Exception('insufficent color values %s' % len(_cs))

        _colors[float(_vs[0])] = _cs if len(_cs) <= 4 else _cs[:4]

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
