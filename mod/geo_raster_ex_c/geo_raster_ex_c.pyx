

from osgeo import gdal, ogr, osr
import os
import re
import math
import numpy as np
cimport numpy as np
cimport cython
import logging
import numpy

from . import geo_raster as ge
from . import geo_base as gb
from . import file_mag
from gio.geo_base import geo_point, geo_polygon, geo_extent, projection_transform

@cython.boundscheck(False)

def to_dtype(pixel_type):
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
                if (min_val is None or _o >= min_val) and (max_val is None or _o <= max_val):
                    continue

            _x, _y = prj.project(_col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            # if (min_val is not None and _v < min_val):
            #     continue
            # if (max_val is not None and _v > max_val):
            #     continue

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
                if (min_val is None or _o >= min_val) and (max_val is None or _o <= max_val):
                    continue

            _x, _y = prj.project(_col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            # if (min_val is not None and _v < min_val):
            #     continue
            # if (max_val is not None and _v > max_val):
            #     continue

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
                if (min_val is None or _o >= min_val) and (max_val is None or _o <= max_val):
                    continue

            _x, _y = prj.project(_col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            # if (min_val is not None and _v < min_val):
            #     continue
            # if (max_val is not None and _v > max_val):
            #     continue

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
                if (min_val is None or _o >= min_val) and (max_val is None or _o <= max_val):
                    continue

            _x, _y = prj.project(_col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            # if (min_val is not None and _v < min_val):
            #     continue
            # if (max_val is not None and _v > max_val):
            #     continue

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
                if (min_val is None or _o >= min_val) and (max_val is None or _o <= max_val):
                    continue

            _x, _y = prj.project(_col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            # if (min_val is not None and _v < min_val):
            #     continue
            # if (max_val is not None and _v > max_val):
            #     continue

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
                if (min_val is None or _o >= min_val) and (max_val is None or _o <= max_val):
                    continue

            _x, _y = prj.project(_col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            # if (min_val is not None and _v < min_val):
            #     continue
            # if (max_val is not None and _v > max_val):
            #     continue

            dat_out[_row, _col] = _v

def read_block_float64(np.ndarray[np.float64_t, ndim=2] dat, ext, prj, geo, float nodata,
        int row_start, np.ndarray[np.float64_t, ndim=2] dat_out, min_val=None, max_val=None):
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
            if (not numpy.isnan(_o)) and _o != nodata:
                if (min_val is None or _o >= min_val) and (max_val is None or _o <= max_val):
                    continue

            _x, _y = prj.project(_col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if numpy.isnan(_v) or _v == nodata:
                continue

            # if (min_val is not None and _v < min_val):
            #     continue
            # if (max_val is not None and _v > max_val):
            #     continue

            dat_out[_row, _col] = _v

class band_file:

    def __init__(self, f, band_idx=1, dataset_name=None, file_unzip=None, cache=None):
        self.file = f
        self.dataset_name = dataset_name
        self.band_idx = band_idx
        self.unzip = file_unzip
        self.band = None
        self.cache = cache

    def get_band(self):
        logging.debug('loading %s' % self.file)
        if self.band:
            return self.band

        _img = None
        _inp = self.file
        _pat = None

        if self.cache:
            _key = _inp[:-3] if _inp.endswith('.gz') else _inp
            _pat = self.cache.get(_key)

            if not _pat:
                if _inp.endswith('.gz'):
                    if not self.unzip:
                        raise Exception('file unzip is required for *.gz files')
                    _inp = self.unzip.unzip(self.file)

                _pat = self.cache.put(_key, _inp)
        else:
            if _inp.endswith('.gz'):
                if not self.unzip:
                    raise Exception('file unzip is required for *.gz files')
                _inp = self.unzip.unzip(self.file)
            _pat = _inp

        assert(_pat)
        _img = ge.open(_pat)

        if _img is None:
            raise Exception('Failed to open image ' + self.file)

        if self.dataset_name:
            _img = _img.get_subdataset(self.dataset_name)
            if _img is None:
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
            if _proj is None:
                _proj = _b.poly.proj

        self.last_band = None
        self.proj = _proj
        self.check_layers = check_layers
        self.nodata = nodata
        self.color_table = None
        self.estimate_params_from_band()

        logging.debug('build geo_band_stack (bands: %s, nodata: %s -> %s)' % (len(bands), nodata, self.nodata))

    def estimate_params_from_band(self):
        if len(self.bands) == 0:
            raise Exception('No band loaded')

        _bnd = self.bands[0].get_band()
        if self.nodata is None:
            self.nodata = _bnd.band.get_nodata()

        self.pixel_type = _bnd.band.pixel_type
        self.cell_size = _bnd.band.geo_transform[1]
        self.cell_size_y = _bnd.band.geo_transform[5]
        self.color_table = _bnd.band.color_table
        self.bands[0].clean()

    @staticmethod
    def from_list(f_list, band_idx=1, dataset_name=None, \
            file_unzip=None, check_layers=False, nodata=None, cache=None):
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

            _bnd = band_file(_file, band_idx, _name, file_unzip, cache)
            _bbb = _bnd.get_band()
            assert(_bbb is not None)

            if _proj is None:
                _proj = _bbb.proj

            _poly = gb.geo_polygon.from_raster(_bbb)
            _bnds.append(geo_band_obj(_poly, _bnd))

        if len(_bnds) == 0:
            logging.debug('No images found')
            return None

        return geo_band_stack_zip(_bnds, _proj, check_layers, nodata)

    @staticmethod
    def from_shapefile(f_list, band_idx=1, dataset_name=None, \
            file_unzip=None, check_layers=False, nodata=None, cache=None, extent=None):
        logging.debug('loading from %s' % f_list)

        if isinstance(f_list, file_mag.obj_mag):
            _finp = f_list.get()
        elif f_list.startswith('s3://'):
            logging.debug('loading s3 file %s' % f_list)
            _finp = file_mag.get(f_list).get()
        else:
            _finp = f_list

        if not _finp:
            raise Exception('no valid file path provide %s' % _finp)

        if _finp.startswith('/') and (not os.path.exists(_finp)):
            raise Exception('failed to find %s' % _finp)

        _bnds = []
        _shp = ogr.Open(_finp)
        if _shp is None:
            logging.error('failed to load shapefile (%s)' % _finp)
            raise Exception('Failed to load shapefile ' + _finp)

        _lyr = _shp.GetLayer()

        if extent:
            _ext = extent
            if isinstance(_ext, ge.geo_raster_info):
                _ext = extent.extent().to_polygon().segment_ratio(10)

            _ext = _ext.project_to(_lyr.GetSpatialRef())
            if _ext is None:
                return None

            if isinstance(_ext, gb.geo_point):
                _lyr.SetSpatialFilter(_ext.to_geometry())
            else:
                _lyr.SetSpatialFilter(_ext.poly)

        _d_shp = os.path.dirname(_finp)

        _file_columns = [_col.name for _col in _lyr.schema if _col.name.lower() == 'file']
        if len(_file_columns) != 1:
            raise Exception('failed to find the FILE column in the shapefile (%s)' % \
                    ','.join([_col.name for _col in _lyr.schema]))

        for _f in _lyr:
            _geo = _f.geometry()
            if _geo is None:
                continue

            _poly = gb.geo_polygon(_geo.Clone())
            _file = _f.items()[_file_columns[0]]
            _file = _file.strip() if _file else None

            if not _file:
                continue

            if not (_file[0] == '/' or _file[1] == ':' or _file.startswith('s3://')):
                # handle relative path
                _file = _d_shp + os.sep + _file

            # support dataset name from the file path
            _name = dataset_name
            if (not _name) and '#' in _file:
                _ns = _file.split('#')
                _file = _ns[0]
                _name = _ns[1]

            _bnds.append(geo_band_obj(_poly, band_file(_file,
                band_idx, _name, file_unzip, cache)))

        if len(_bnds) == 0:
            logging.debug('No images loaded')
            return None

        logging.debug('loaded %s tiles' % len(_bnds))
        return geo_band_stack_zip(_bnds, _lyr.GetSpatialRef(), check_layers, nodata)

    def clean(self):
        for _b in self.bands:
            if _b.band is not None:
                _b.clean()

    def get_band(self, pt):
        if self.last_band is not None and self.bands[self.last_band].poly.is_contain(pt):
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
        if self.last_band is not None and self.bands[self.last_band].poly.is_contain(_pt):
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
        if self.last_band is not None:
            _v = self.bands[self.last_band].get_band().read(x, y, cache)
            if _v is not None:
                return _v

        _pt = geo_point(x, y)
        for i in xrange(len(self.bands)):
            if i == self.last_band:
                continue

            if not self.bands[i].poly.is_contain(_pt):
                continue

            _v = self.bands[i].get_band().read(x, y, cache)
            if self.check_layers == False or not _v is None:
                self.last_band = i
                return _v

        return None

    def read(self, pt, cache=False):
        _v = None
        if self.last_band is not None:
            _v = self.bands[self.last_band].get_band(
                        ).read_point(pt, cache)

            if _v is not None:
                return _v

        for i in xrange(len(self.bands)):
            if i == self.last_band:
                continue

            if not self.bands[i].poly.is_contain(pt):
                continue

            _v = self.bands[i].get_band().read_point(pt, cache)
            if self.check_layers == False or _v is not None:
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
                    logging.debug('add band %s' % self.bands[i].band_file.file)
                    _ls.append(self.bands[i])
                    break

        return _ls

    def _read_band(self, bnd, bnd_info, nodata, pol_t1, dat_out, min_val=None, max_val=None):
        _buffer_dist = 1.0E-15

        _bnd_info = bnd_info
        _nodata = nodata

        _dat_out = dat_out
        if _dat_out is None:
            return

        _pol_t1 = pol_t1

        _bnd = _bnd_info.get_band().band
        logging.debug('loading file %s' % _bnd_info.band_file.file)
        _pol_s = gb.geo_polygon.from_raster(_bnd, div=100)

        if _pol_s is None:
            logging.debug('skip file #1 %s' % _bnd_info.band_file.file)
            return

        # calculate the intersection area for both data sets
        _pol_t1_proj = _pol_t1.project_to(_bnd.proj)
        if _pol_t1_proj is None or _pol_t1_proj.poly is None:
            logging.debug('skip file #2 %s' % _bnd_info.band_file.file)
            return
        # _pol_t1_proj = _pol_t1_proj.buffer(_buffer_dist)

        if not _pol_s.extent().is_intersect(_pol_t1_proj.extent()):
            return

        _pol_c_s = _pol_s.intersect(_pol_t1_proj)
        if _pol_c_s.poly is None:
            _pol_c_s = _pol_s.buffer(_buffer_dist).intersect(_pol_t1_proj.buffer(_buffer_dist))
            logging.debug('apply buffer to solve geometric conflicts')

        if _pol_c_s.poly is None:
            logging.debug('skip file #3 %s' % _bnd_info.band_file.file)
            return

        _pol_c_s.set_proj(_bnd.proj)
        _pol_c_t = _pol_c_s.project_to(bnd.proj)

        if _pol_c_t is None or _pol_c_t.poly is None:
            logging.debug('failed to reproject the extent')
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

        if _row_s_s > _row_s_e:
            return

        # _col_s_s, _col_s_e = max(0, _col_s_s-1), min(_bnd.width, _col_s_e+1)
        # _row_s_s, _row_s_e = max(0, _row_s_s-1), min(_bnd.height,_row_s_e+1)

        _ext_s_cs = geo_extent(_col_s_s, _row_s_s, _col_s_e, _row_s_e)

        # only load the intersection area to reduce memory use
        _row_s_s = max(0, _row_s_s - 1)

        _dat = _bnd.read_rows(_row_s_s,
                min(_row_s_e + 2, _bnd.height) - _row_s_s)
        if _dat is None:
            return

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
        elif self.pixel_type == 7:
            read_block_float64(_dat, _ext_t_cs, _prj, _bnd.geo_transform,
                    _nodata, _row_s_s, _dat_out, min_val, max_val)
        else:
            raise Exception('The pixel type is not supported ' + \
                    str(self.pixel_type))

    def read_block(self, bnd, use_pts=False, min_val=None, max_val=None):
        _default_nodata = {1: 255, 2: 65535, 3: -9999, 4: (2 ** 32) - 1, 5: -9999, 6: -9999, 7: numpy.nan}
        if self.pixel_type not in _default_nodata.keys():
            raise Exception('Unsupport data type %s' % self.pixel_type)

        _dat_out = np.empty([bnd.height, bnd.width], dtype=to_dtype(self.pixel_type))

        _nodata = self.nodata
        if _nodata is None:
            _nodata = _default_nodata[self.pixel_type]
            logging.debug('No nodata value provided, using default value (%s)' % _nodata)

        _dat_out.fill(_nodata)

        logging.debug('reading block from "%s" to "%s"' % (\
            self.proj.ExportToProj4(),
            bnd.proj.ExportToProj4()))

        # _pol_t1 = gb.geo_polygon.from_raster(bnd, div=100).buffer(0.0)
        _pol_t1 = gb.geo_polygon.from_raster(bnd, div=100)
        if _pol_t1 is None or _pol_t1.poly is None:
            return None

        _pol_t2 = _pol_t1.project_to(self.proj)
        if _pol_t2 is None or _pol_t2.poly is None:
            return None

        if use_pts:
            logging.debug('enable using PTS')

            _pts_t1 = _pol_t1.get_points(self.proj)
            _bnds = self.get_bands_pts(_pts_t1)
        else:
            _bnds = self.get_bands(_pol_t2)

        logging.debug('found %s bands' % len(_bnds))
        for _bnd_info in _bnds:
            self._read_band(bnd, _bnd_info, _nodata, _pol_t1, _dat_out, min_val, max_val)
            _bnd_info.clean()

        return ge.geo_band_cache(_dat_out, bnd.geo_transform, bnd.proj, _nodata, \
                self.pixel_type, self.color_table)

class geo_band_reader:

    def __init__(self, band, name=None):
        self.name = name
        self.band = band
        self.raster = band.raster

        self.poly = gb.geo_polygon.from_raster(self.raster)

    def read(self, float x, float y, cache=False):
        _val = self.band.read_location_cache(x, y) if cache else self.band.read_location(x, y)

        if _val is None or _val == self.band.nodata:
            return None

        return _val

    def read_point(self, pt, cache=False):
        _pt = pt.project_to(self.raster.proj)
        if _pt is None:
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
                if _v is None or _v == self.band.nodata:
                    continue

                _vs.append(_v)

        if not len(_vs):
            return None, 0

        return sum(_vs) / len(_vs), max(_vs) - min(_vs)

    def read_ext(self, pt, dist=1):
        _v_o = self.read_point(pt)
        if _v_o is None:
            return None, 0

        _col_o, _row_o = self.raster.to_cell(pt.x, pt.y)
        _vs = []
        for _row in xrange(_row_o - dist, _row_o + dist + 1):
            for _col in xrange(_col_o - dist, _col_o + dist + 1):
                if 0 <= _row < self.band.height and 0 <= _col < self.band.width:
                    _v = self.band.read_cell(_col, _row)
                    if _v is None or _v == self.banGetAread.nodata:
                        continue

                    _vs.append(_v)

        return _v_o, max(_vs) - min(_vs)

def collect_samples(bnd_landsat, proj, interval=3000):
    _img_landsat = bnd_landsat.raster
    _read_landsat = geo_band_reader(bnd_landsat)

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

            if _vl is None:
                continue

            _vs.append(_pt)

    return _vs

def modis_projection():
    _modis_proj = osr.SpatialReference()
    _modis_proj.ImportFromProj4('+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs')

    return _modis_proj

def read_block(f, bnd):
    _bnd = load(f, bnd)

    if _bnd is None:
        return None

    return _bnd.read_block(bnd)

def load(f, bnd=None):
    if not f:
        return None

    _f = str(f)
    if _f.endswith('.shp') or _f.startswith('PG:'):
        logging.debug('loading geo_band_stack %s' % _f)
        _shp = geo_band_stack_zip.from_shapefile(f, extent=bnd)
        return _shp

    _img = ge.open(f)
    if _img is None:
        return None

    return _img.get_band()
