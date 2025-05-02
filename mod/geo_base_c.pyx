'''
File: geo_base_c.py
Author: Min Feng
Version: 0.1
Create: 2013-03-26 18:01:16
Description: Provide the basic geometry objects, retrieved from geo_raster_ex
'''

import sys
_inf = sys.float_info.max

import osgeo
from osgeo import osr
from osgeo import ogr, gdal
import logging

cimport numpy as np
cimport cython
import numpy

@cython.boundscheck(False)

cdef void update_cc(self, int row, int col):
    cdef list _mat = self.mat
    cdef list _vs = _mat[row][col]

    if not (_vs[2] >= _inf or _vs[3] >= _inf):
        return
    
    if self.proj_src is None or self.proj_tar is None:
        raise Exception('exceeded the projection extent')

    _pt0 = geo_point(_vs[0], _vs[1], self.proj_src)
    _pt1 = _pt0.project_to(self.proj_tar)

    if _pt1 is None:
        raise Exception('failed to reproject control point')

    _mat[row][col][2] = _pt1.x
    _mat[row][col][3] = _pt1.y

cdef (float, float) project(self, int col, int row):
    cdef float _scale = self.scale
    cdef int _col0 = int(col / _scale)
    cdef int _row0 = int(row / _scale)

    cdef int _row1 = _row0 + 1
    cdef int _col1 = _col0 + 1

    cdef float _del_x = col / _scale - _col0
    cdef float _del_y = row / _scale - _row0

    update_cc(self, _row0, _col0)
    update_cc(self, _row0, _col1)
    update_cc(self, _row1, _col0)
    update_cc(self, _row1, _col1)

    cdef list _mat = self.mat
    # print col, row, _col0, _row0, self.mat.shape
    cdef float _mat_00x = _mat[_row0][_col0][2]
    cdef float _mat_01x = _mat[_row0][_col1][2]
    cdef float _mat_10x = _mat[_row1][_col0][2]
    cdef float _mat_11x = _mat[_row1][_col1][2]

    if _mat_00x >= _inf or _mat_01x >= _inf or _mat_10x >= _inf or _mat_11x >= _inf:
        # print _inf, _mat_00x, _mat_01x, _mat_10x, _mat_11x
        # print _mat_00x >= _inf, _mat_01x >= _inf, _mat_10x >= _inf, _mat_11x >= _inf

        raise Exception('exceeded the projection extent')

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

def from_dtype(dtype):
    if dtype == numpy.uint8:
        return 1
    if dtype == numpy.uint16:
        return 2
    if dtype == numpy.int16:
        return 3
    if dtype == numpy.uint32:
        return 4
    if dtype == numpy.int32:
        return 5
    if dtype == numpy.float32:
        return 6
    if dtype == numpy.float64:
        return 7

    raise Exception('unknown dtype %s' % dtype)

cdef (int, int) to_cell(tuple g, float x, float y):
    '''Convert coordinate to col and row'''
    return int((x - g[0]) / g[1]), int((y - g[3]) / g[5])

def read_block_uint8(np.ndarray[np.uint8_t, ndim=2] dat, ext, prj, geo, unsigned int nodata, int row_start, np.ndarray[np.uint8_t, ndim=2] dat_out):
    cdef int _row, _col
    cdef float _x=_inf, _y=_inf
    cdef int _c, _r

    cdef int _rows_in = dat.shape[0]
    cdef int _cols_in = dat.shape[1]

    cdef int _rows_ot = dat_out.shape[0]
    cdef int _cols_ot = dat_out.shape[1]

    cdef unsigned int _v

    cdef int _col_min = max(0, ext.minx)
    cdef int _col_max = min(_cols_ot, ext.maxx + 1)
    cdef int _row_min = max(0, ext.miny)
    cdef int _row_max = min(_rows_ot, ext.maxy + 1)

    for _row in xrange(_row_min, _row_max):
        for _col in xrange(_col_min, _col_max):
            # _x, _y = prj.project(_col, _row)
            _x, _y = project(prj, _col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            dat_out[_row, _col] = _v

def read_block_uint16(np.ndarray[np.uint16_t, ndim=2] dat, ext, prj, geo, int nodata, int row_start, np.ndarray[np.uint16_t, ndim=2] dat_out):
    cdef int _row, _col
    cdef float _x, _y
    cdef int _c, _r

    cdef int _rows_in = dat.shape[0]
    cdef int _cols_in = dat.shape[1]

    cdef int _rows_ot = dat_out.shape[0]
    cdef int _cols_ot = dat_out.shape[1]

    cdef unsigned short _v

    cdef int _col_min = max(0, ext.minx)
    cdef int _col_max = min(_cols_ot, ext.maxx + 1)
    cdef int _row_min = max(0, ext.miny)
    cdef int _row_max = min(_rows_ot, ext.maxy + 1)

    for _row in xrange(_row_min, _row_max):
        for _col in xrange(_col_min, _col_max):
            # _x, _y = prj.project(_col, _row)
            _x, _y = project(prj, _col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            dat_out[_row, _col] = _v

def read_block_int16(np.ndarray[np.int16_t, ndim=2] dat, ext, prj, geo, int nodata, int row_start, np.ndarray[np.int16_t, ndim=2] dat_out):
    cdef int _row, _col
    cdef float _x, _y
    cdef int _c, _r

    cdef int _rows_in = dat.shape[0]
    cdef int _cols_in = dat.shape[1]

    cdef int _rows_ot = dat_out.shape[0]
    cdef int _cols_ot = dat_out.shape[1]

    cdef short _v

    cdef int _col_min = max(0, ext.minx)
    cdef int _col_max = min(_cols_ot, ext.maxx + 1)
    cdef int _row_min = max(0, ext.miny)
    cdef int _row_max = min(_rows_ot, ext.maxy + 1)

    for _row in xrange(_row_min, _row_max):
        for _col in xrange(_col_min, _col_max):
            # _x, _y = prj.project(_col, _row)
            _x, _y = project(prj, _col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            dat_out[_row, _col] = _v

def read_block_uint32(np.ndarray[np.uint32_t, ndim=2] dat, ext, prj, geo, int nodata, int row_start, np.ndarray[np.uint32_t, ndim=2] dat_out):
    cdef int _row, _col
    cdef float _x, _y
    cdef int _c, _r

    cdef int _rows_in = dat.shape[0]
    cdef int _cols_in = dat.shape[1]

    cdef int _rows_ot = dat_out.shape[0]
    cdef int _cols_ot = dat_out.shape[1]

    cdef unsigned int _v

    cdef int _col_min = max(0, ext.minx)
    cdef int _col_max = min(_cols_ot, ext.maxx + 1)
    cdef int _row_min = max(0, ext.miny)
    cdef int _row_max = min(_rows_ot, ext.maxy + 1)

    for _row in xrange(_row_min, _row_max):
        for _col in xrange(_col_min, _col_max):
            # _x, _y = prj.project(_col, _row)
            _x, _y = project(prj, _col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            dat_out[_row, _col] = _v

def read_block_int32(np.ndarray[np.int32_t, ndim=2] dat, ext, prj, geo, int nodata, int row_start, np.ndarray[np.int32_t, ndim=2] dat_out):
    cdef int _row, _col
    cdef float _x, _y
    cdef int _c, _r

    cdef int _rows_in = dat.shape[0]
    cdef int _cols_in = dat.shape[1]

    cdef int _rows_ot = dat_out.shape[0]
    cdef int _cols_ot = dat_out.shape[1]

    cdef int _v

    cdef int _col_min = max(0, ext.minx)
    cdef int _col_max = min(_cols_ot, ext.maxx + 1)
    cdef int _row_min = max(0, ext.miny)
    cdef int _row_max = min(_rows_ot, ext.maxy + 1)

    for _row in xrange(_row_min, _row_max):
        for _col in xrange(_col_min, _col_max):
            # _x, _y = prj.project(_col, _row)
            _x, _y = project(prj, _col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            dat_out[_row, _col] = _v

def read_block_float32(np.ndarray[np.float32_t, ndim=2] dat, ext, prj, geo, float nodata, int row_start, np.ndarray[np.float32_t, ndim=2] dat_out):
    cdef int _row, _col
    cdef float _x, _y
    cdef int _c, _r

    cdef int _rows_in = dat.shape[0]
    cdef int _cols_in = dat.shape[1]

    cdef int _rows_ot = dat_out.shape[0]
    cdef int _cols_ot = dat_out.shape[1]

    cdef float _v

    cdef int _col_min = max(0, ext.minx)
    cdef int _col_max = min(_cols_ot, ext.maxx + 1)
    cdef int _row_min = max(0, ext.miny)
    cdef int _row_max = min(_rows_ot, ext.maxy + 1)

    for _row in xrange(_row_min, _row_max):
        for _col in xrange(_col_min, _col_max):
            # _x, _y = prj.project(_col, _row)
            _x, _y = project(prj, _col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            dat_out[_row, _col] = _v

def read_block_float64(np.ndarray[np.float64_t, ndim=2] dat, ext, prj, geo, float nodata, int row_start, np.ndarray[np.float64_t, ndim=2] dat_out):
    cdef int _row, _col
    cdef float _x, _y
    cdef int _c, _r

    cdef int _rows_in = dat.shape[0]
    cdef int _cols_in = dat.shape[1]

    cdef int _rows_ot = dat_out.shape[0]
    cdef int _cols_ot = dat_out.shape[1]

    cdef float _v

    cdef int _col_min = max(0, ext.minx)
    cdef int _col_max = min(_cols_ot, ext.maxx + 1)
    cdef int _row_min = max(0, ext.miny)
    cdef int _row_max = min(_rows_ot, ext.maxy + 1)

    for _row in xrange(_row_min, _row_max):
        for _col in xrange(_col_min, _col_max):
            # _x, _y = prj.project(_col, _row)
            _x, _y = project(prj, _col, _row)

            _c, _r = to_cell(geo, _x, _y)
            _r -= row_start

            if not (0 <= _c < _cols_in and 0 <= _r < _rows_in):
                continue

            _v = dat[_r, _c]
            if _v == nodata:
                continue

            dat_out[_row, _col] = _v

class geo_object:

    def __init__(self, proj):
        self.proj = proj

    @property
    def proj(self):
        return proj_from_wkt(self._proj)
    
    @proj.setter
    def proj(self, val):
        if val is None:
            self._proj = None
        else:
            self._proj = val.ExportToWkt()

class geo_extent (geo_object):

    @classmethod
    def from_raster(cls, img):
        _geo = img.geo_transform

        _pt1 = (_geo[0], _geo[3])
        _pt2 = (_geo[0] + img.width * _geo[1] + img.height * _geo[2], _geo[3] + img.width * _geo[4] + img.height * _geo[5])

        return cls(_pt1[0], _pt2[1], _pt2[0], _pt1[1], img.proj)

    def __init__(self, x1=-180, y1=-90, x2=180, y2=90, proj=None):
        geo_object.__init__(self, proj)
        
        self.minx = min(x1, x2)
        self.maxx = max(x1, x2)
        self.miny = min(y1, y2)
        self.maxy = max(y1, y2)

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

    def buffer(self, dist):
        return geo_extent(self.minx - dist, self.miny - dist, self.maxx + dist, self.maxy + dist)

    def is_contain(self, pt):
        if pt.x < self.minx or pt.x > self.maxx or pt.y < self.miny or pt.y > self.maxy:
            return False

        return True

    def intersect(self, extent):
        return geo_extent(max(self.minx, extent.minx), max(self.miny, extent.miny), \
                min(self.maxx, extent.maxx), min(self.maxy, extent.maxy), self.proj)

    def union(self, extent):
        return geo_extent(min(self.minx, extent.minx), min(self.miny, extent.miny), \
                max(self.maxx, extent.maxx), max(self.maxy, extent.maxy), self.proj)

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

class geo_polygon (geo_object):

    def __init__(self, poly, proj=None):
        _proj = poly.GetSpatialReference()
        if proj is not None:
            _proj = proj
            poly.AssignSpatialReference(_proj)
            
        geo_object.__init__(self, _proj)
        self.poly = poly

    @classmethod
    def from_raster(cls, img, div=10):
        if div <= 0:
            raise Exception('segment number needs to be larger than 0')

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

        for _c in xrange(div - 1):
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

        if len(pts) <= 2:
            raise Exception('need at least 3 points (%s) to create a polygon' % len(pts))

        _proj = fix_geog_axis(proj)
        _ring = ogr.Geometry(ogr.wkbLinearRing)
        for _pt in pts:
            _ring.AddPoint(_pt.x, _pt.y)
            if _proj is not None and _pt.proj is not None:
                _proj = _pt.proj

        if pts[-1].x != pts[0].x or pts[-1].y != pts[0].y:
            _ring.AddPoint(pts[0].x, pts[0].y)

        _ring.CloseRings()

        _poly = ogr.Geometry(ogr.wkbPolygon)
        _poly.AddGeometry(_ring)
        _proj and _poly.AssignSpatialReference(_proj)

        return cls(_poly)

    @classmethod
    def from_xys(cls, pts, proj=None):
        from osgeo import ogr

        if len(pts) <= 2:
            raise Exception('need at least 3 points (%s) to create a polygon' % len(pts))

        _proj = fix_geog_axis(proj)
        _ring = ogr.Geometry(ogr.wkbLinearRing)
        for _pt in pts:
            _ring.AddPoint(_pt[0], _pt[1])

        if pts[len(pts) - 1][0] != pts[0][0] or pts[len(pts) - 1][1] != pts[0][1]:
            _ring.AddPoint(pts[0][0], pts[0][1])

        _ring.CloseRings()

        _poly = ogr.Geometry(ogr.wkbPolygon)
        _poly.AddGeometry(_ring)
        _proj and _poly.AssignSpatialReference(_proj)

        return cls(_poly)

    def project_to(self, proj, geo_cut=False):
        if self.proj is None or self.proj.IsSame(proj):
            return self

        _geom_type = self.poly.GetGeometryType()
        if _geom_type == 3:
            return self._project_poly(proj)

        _poly = self.poly.Clone()
        _err = _poly.TransformTo(fix_geog_axis(proj))
        if _err != 0:
            logging.error('failed to project polygon to (%s)' % (proj.ExportToProj4(), ))
            return None

        return geo_polygon(_poly)

    def _project_ring(self, ring, proj_src, proj):
        from osgeo import ogr
        _ring = ogr.Geometry(ogr.wkbLinearRing)

        _pp = ogr.Geometry(ogr.wkbPoint)
        for _i in xrange(ring.GetPointCount()):
            _pt = ring.GetPoint_2D(_i)

            _pp.SetPoint_2D(0, _pt[0], _pt[1])
            _pp.AssignSpatialReference(fix_geog_axis(proj_src))

            if _pp.TransformTo(fix_geog_axis(proj)) != 0:
                continue

            _pt = _pp.GetPoint_2D()
            _ring.AddPoint(_pt[0], _pt[1])

        _ring.CloseRings()
        return _ring

    def _project_poly(self, proj, geo_cut=False):
        from osgeo import ogr

        _poly = ogr.Geometry(ogr.wkbPolygon)
        _poly.AssignSpatialReference(fix_geog_axis(proj))

        _proj = fix_geog_axis(self.proj)
        _pppp = self

        # if '+proj=sinu ' in _proj.ExportToProj4() and proj.IsGeographic():
        if geo_cut and proj.IsGeographic():
            # cut the polygon to avoid exceeding geographic extent
            _pppp = self.intersect( \
                    geo_polygon.from_xys([(-179.999, -89.999), (-179.999, 89.999), (179.999, 89.999), (179.999, -89.999)], \
                    fix_geog_axis(proj)).segment_ratio(300).project_to(self.proj))

        for _r in xrange(_pppp.poly.GetGeometryCount()):
            _poly.AddGeometry(self._project_ring(_pppp.poly.GetGeometryRef(_r), _proj, fix_geog_axis(proj)))

        return geo_polygon(_poly)

    def set_proj(self, proj):
        self.proj = proj

    def union(self, poly):
        _g = self.poly.Union(poly.poly)
        if _g is None:
            return None
        return geo_polygon(_g)

    def intersect(self, poly):
        _g = self.poly.Intersection(poly.poly)
        if _g is None:
            return None
        return geo_polygon(_g)

    def center(self):
        _pt = self.poly.Centroid().GetPoint_2D()
        return geo_point(_pt[0], _pt[1], self.proj)

    def extent(self):
        _ext = self.poly.GetEnvelope()
        return geo_extent(_ext[0], _ext[2], _ext[1], _ext[3], self.proj)

    def area(self):
        return self.poly.GetArea()

    def is_intersect(self, poly):
        _poly1 = self.poly
        _poly2 = poly.poly

        return _poly1.Intersect(_poly2)

    def buffer(self, dis, nsegs=30):
        _poly = geo_polygon(self.poly.Buffer(dis, nsegs))
        if self.proj is not None:
            _poly.set_proj(self.proj)
        return _poly

    def is_contain(self, pt):
        _loc = pt.project_to(self.proj)

        from osgeo import ogr
        _pt = ogr.Geometry(ogr.wkbPoint)
        _pt.SetPoint_2D(0, _loc.x, _loc.y)

        return self.poly.Contains(_pt)

    def split_section_ratio(self, pt_s, pt_e, dis):
        _d_x = (pt_e[0] - pt_s[0]) / dis
        _d_y = (pt_e[1] - pt_s[1]) / dis
        _d_z = (pt_e[1] - pt_s[1]) / dis

        _ps = []

        _x = pt_s[0]
        _y = pt_s[1]
        _z = pt_s[2]

        for _p in range(dis):
            _ps.append((_x, _y, _z))

            _x += _d_x
            _y += _d_y
            _z += _d_z

        return _ps

    def split_section_dis(self, pt_s, pt_e, dis):
        import math
        _dis = math.hypot((pt_s[0] - pt_e[0]), (pt_s[1] - pt_e[1]))
        _div = _dis / dis
        _ddd = int(math.ceil(_div))

        _d_x = (pt_e[0] - pt_s[0]) / _div
        _d_y = (pt_e[1] - pt_s[1]) / _div
        _d_z = (pt_e[1] - pt_s[1]) / _div

        _ps = []

        _x = pt_s[0]
        _y = pt_s[1]
        _z = pt_s[2]

        for _p in xrange(_ddd):
            _ps.append((_x, _y, _z))

            _x += _d_x
            _y += _d_y
            _z += _d_z

        return _ps

    def segment_ratio(self, rat):
        from osgeo import ogr

        _poly = ogr.Geometry(ogr.wkbPolygon)

        for _line in self.poly:
            _cc = _line.GetPointCount()
            _ring = ogr.Geometry(ogr.wkbLinearRing)

            _ps = []

            for i in xrange(_cc - 1):
                _ps.extend(self.split_section_ratio(_line.GetPoint(i), _line.GetPoint(i + 1), rat))

            _ps.append(_line.GetPoint(_cc - 1))

            for _pt in _ps:
                _ring.AddPoint(*_pt)

            _poly.AddGeometry(_ring)

        _proj = self.proj
        _proj and _poly.AssignSpatialReference(_proj)

        return geo_polygon(_poly)

    def segment_dis(self, dis):
        from osgeo import ogr

        _poly = ogr.Geometry(ogr.wkbPolygon)

        for _line in self.poly:
            _cc = _line.GetPointCount()
            _ring = ogr.Geometry(ogr.wkbLinearRing)

            _ps = []
            for i in xrange(_cc - 1):
                _ps.extend(self.split_section_dis(_line.GetPoint(i), _line.GetPoint(i + 1), dis))

            _ps.append(_line.GetPoint(_cc - 1))

            for _pt in _ps:
                _ring.AddPoint(*_pt)

            _poly.AddGeometry(_ring)

        _proj = self.proj
        _proj and _poly.AssignSpatialReference(_proj)

        return geo_polygon(_poly)

    def get_points(self, proj=None):
        _ps = []
        for i in xrange(self.poly.GetGeometryCount()):
            _g = self.poly.GetGeometryRef(i)
            for _p in _g.GetPoints():
                _pt = geo_point(_p[0], _p[1], self.proj)
                if proj is not None:
                    _pt = _pt.project_to(fix_geog_axis(proj))

                if _pt is None:
                    continue

                _ps.append(_pt)

        return _ps

class geo_point (geo_object):
    @classmethod
    def from_raster(cls, raster, col, row):
        _x, _y = raster.to_location(col, row)
        return cls(_x, _y, raster.proj)

    def __init__(self, x, y, proj=None):
        geo_object.__init__(self, proj)
        self.put_pt(x, y)

    def put_pt(self, x, y):
        self.x = x
        self.y = y
        self.geom = None

    def get_pt(self):
        return self.x, self.y

    def project_to(self, proj):
        _proj = fix_geog_axis(proj)

        if self.proj is None or self.proj.IsSame(_proj):
            return self

        _pt = self.to_geometry()
        _err = _pt.TransformTo(_proj)
        if _err != 0:
            logging.error('failed to project pt (%s, %s) to (%s)' % (self.x, self.y, _proj.ExportToProj4()))
            return None

        _pt = _pt.GetPoint_2D()
        return geo_point(_pt[0], _pt[1], proj=_proj)

    def to_geometry(self):
        if self.geom is None:
            from osgeo import ogr
            self.geom = ogr.Geometry(ogr.wkbPoint)

        self.geom.SetPoint_2D(0, self.x, self.y)
        if self.proj is not None:
            self.geom.AssignSpatialReference(self.proj)

        return self.geom

    def distance_to(self, pt):
        _pt = pt.project_to(self.proj)
        return ((self.x - _pt.x) ** 2 + (self.y - _pt.y) ** 2) ** 0.5

    def __str__(self):
        return '%f, %f' % (self.x, self.y)

    def __eq__(self, pt):
        if pt is None:
            return False

        return (self.x == pt.x and self.y == pt.y and (self.proj is None or self.proj.IsSame(pt.proj) == 1))

class projection_transform:
    ''' Build a grid for transforming raster pixels'''

    @classmethod
    def from_band(cls, bnd_info, proj, interval=10, f_pts0=None, f_pts1=None, delay_reproj=True):
        import math
        from . import geo_raster

        # make sure there are at least 1 points for each axis
        # _scale = min((bnd_info.width / 1.0, bnd_info.height / 1.0, float(interval)))
        _scale = min(bnd_info.width / interval, bnd_info.height / interval)

        if _scale <= 0:
            logging.error('using raster that is too small (%s, %s)' % (bnd_info.width, bnd_info.height))
            raise Exception('using raster that is too small (%s, %s)' % (bnd_info.width, bnd_info.height))

        _img_w = int(math.ceil(bnd_info.width / _scale)) + 1
        _img_h = int(math.ceil(bnd_info.height / _scale)) + 1

        # logging.debug('scale: %s, size: %s, %s' % (_scale, _img_w, _img_h))

        _ms = []

        # output the points for debugging
        _pts0 = []
        _pts1 = []

        for _row in xrange(_img_h):
            _mm = []
            for _col in xrange(_img_w):
                _pt0 = geo_raster.to_location(bnd_info.geo_transform, _col * _scale, _row * _scale)

                _pt0 = geo_point(_pt0[0], _pt0[1], bnd_info.proj)
                _pts0.append(_pt0)

                _pt1 = None if delay_reproj else _pt0.project_to(proj)

                if _pt1 is None:
                    _mm.append([_pt0.x, _pt0.y, _inf, _inf])
                else:
                    _mm.append([_pt0.x, _pt0.y, _pt1.x, _pt1.y])
                    _pts1.append(_pt1)

            _ms.append(_mm)

        # logging.debug('points number: %s' % len(_pts0))

        f_pts0 and output_points(_pts0, f_pts0)
        f_pts1 and output_points(_pts1, f_pts1)

        # output_points(_pts0, 'point0.shp')
        # output_points(_pts1, 'point1.shp')

        return cls(_ms, _scale, bnd_info.proj, proj)

    @classmethod
    def from_extent(cls, ext, proj, dist=1000.0):
        import math

        # make sure there are at least 1 points for each axis
        _scale = min((ext.width() / 1.0, ext.height() / 1.0, float(dist)))
        if _scale <= 0:
            logging.error('using raster that is too small (%s, %s)' % (ext.width() / 1.0, ext.height() / 1.0))
            raise Exception('using raster that is too small (%s, %s)' % (ext.width() / 1.0, ext.height() / 1.0))

        _img_w = int(math.ceil(ext.width() / _scale)) + 1
        _img_h = int(math.ceil(ext.height() / _scale)) + 1

        _ms = []
        _y = ext.miny
        for _row in xrange(_img_h):
            _mm = []
            _x = ext.minx
            for _col in xrange(_img_w):
                _pt0 = geo_point(_x, _y, ext.proj)
                _mm.append([_pt0.x, _pt0.y, _inf, _inf])

                # _pt1 = _pt0.project_to(proj)
                # if _pt1 is None:
                #     continue
                #
                # _mm.append([_pt0.x, _pt0.y, _pt1.x, _pt1.y])

                _x += dist

            _ms.append(_mm)
            _y += dist

        return cls(_ms, _scale, ext.proj, proj)

    def __init__(self, mat, scale, proj_src=None, proj_tar=None):
        self.mat = mat
        self.scale = float(scale)

        self.proj_src = fix_geog_axis(proj_src)
        self.proj_tar = fix_geog_axis(proj_tar)

    def _update_cc(self, row, col):
        _vs = self.mat[row][col]
        if _vs[2] >= _inf or _vs[3] >= _inf:
            if self.proj_src is None or self.proj_tar is None:
                raise Exception('exceeded the projection extent')

            _pt0 = geo_point(_vs[0], _vs[1], self.proj_src)
            _pt1 = _pt0.project_to(self.proj_tar)

            if _pt1 is None:
                raise Exception('failed to reproject control point')

            self.mat[row][col][2] = _pt1.x
            self.mat[row][col][3] = _pt1.y

    def project(self, int col, int row):
        cdef float _scale = self.scale
        cdef int _col0 = int(col / _scale)
        cdef int _row0 = int(row / _scale)

        cdef int _row1 = _row0 + 1
        cdef int _col1 = _col0 + 1

        cdef float _del_x = col / _scale - _col0
        cdef float _del_y = row / _scale - _row0

        self._update_cc(_row0, _col0)
        self._update_cc(_row0, _col1)
        self._update_cc(_row1, _col0)
        self._update_cc(_row1, _col1)

        cdef list _mat = self.mat
        # print col, row, _col0, _row0, self.mat.shape
        cdef float _mat_00x = _mat[_row0][_col0][2]
        cdef float _mat_01x = _mat[_row0][_col1][2]
        cdef float _mat_10x = _mat[_row1][_col0][2]
        cdef float _mat_11x = _mat[_row1][_col1][2]

        if _mat_00x >= _inf or _mat_01x >= _inf or _mat_10x >= _inf or _mat_11x >= _inf:
            # print _inf, _mat_00x, _mat_01x, _mat_10x, _mat_11x
            # print _mat_00x >= _inf, _mat_01x >= _inf, _mat_10x >= _inf, _mat_11x >= _inf

            raise Exception('exceeded the projection extent')

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

def modis_proj():
    return '+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs'

def modis_projection():
    return proj_from_proj4(modis_proj())

def proj_from_proj4(txt):
    if not txt:
        return None

    import re
    _m = re.match(r'EPSG:(\d+)', txt.upper())
    if _m:
        return proj_from_epsg(int(_m.group(1)))

    _proj = osr.SpatialReference()
    _proj.ImportFromProj4(str(txt))

    return fix_geog_axis(_proj)

def proj_from_epsg(code=4326):
    _proj = osr.SpatialReference()
    _proj.ImportFromEPSG(code)

    return fix_geog_axis(_proj)

def proj_from_wkt(txt):
    if not txt:
        return None
    
    _proj = osr.SpatialReference()
    _proj.ImportFromWkt(txt)

    return fix_geog_axis(_proj)

def fix_geog_axis(proj):
    if not proj:
        return proj

    if int(osgeo.__version__[0]) >= 3:
        if hasattr(proj, 'fixed_proj') and proj.fixed_proj:
            return proj

        proj.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
        proj.fixed_proj = True
    return proj

def output_geometries(geos, proj, geo_type, f_shp):
    import os
    
    _drv_type = 'ESRI Shapefile'
    if f_shp.lower().endswith('.kml'):
        _drv_type = 'KML'
    if f_shp.lower().endswith('.geojson'):
        _drv_type = 'GeoJSON'

    logging.info('output shapefile to %s (%s)' % (f_shp, _drv_type))

    _drv = ogr.GetDriverByName(_drv_type)
    if os.path.exists(f_shp):
        _drv.DeleteDataSource(f_shp)

    _shp = _drv.CreateDataSource(f_shp)
    if _shp is None:
        logging.error('failed to create file %s' % f_shp)
        return

    _tag = os.path.splitext(os.path.basename(f_shp))[0]
    _lyr = _shp.CreateLayer(_tag, proj, geo_type)
    if _shp is None:
        logging.error('failed to create create %s' % _tag)
        return

    for _geo in geos:
        _fea = ogr.Feature(_lyr.GetLayerDefn())
        _fea.SetGeometry(_geo)
        _lyr.CreateFeature(_fea)
        _fea.Destroy()

def output_points(pts, f_shp):
    from osgeo import ogr, gdal

    if len(pts) == 0: return
    logging.debug('output points to ' + f_shp)
    output_geometries([_pt.to_geometry() for _pt in pts], pts[0].proj, ogr.wkbPoint, f_shp)

def output_polygons(polys, f_shp):
    from osgeo import ogr, gdal

    if len(polys) == 0: return
    logging.debug('output polygon to ' + f_shp)
    output_geometries([_poly.poly for _poly in polys], polys[0].proj, ogr.wkbPolygon, f_shp)

def load_shp(f, ext=None, layer_name=None):
    from osgeo import ogr
    from . import file_mag

    if isinstance(ext, (str, file_mag.obj_mag)):
        ext = [_g for _g, _ in load_shp(ext)]

    if isinstance(ext, (list, tuple)):
        _ids = []

        for _q in ext:
            for _g, _s in load_shp(f, _q, layer_name):
                _id = _s['FID']

                if _id in _ids:
                    continue

                _ids.append(_id)
                yield _g, _s
        return

    _shp = ogr.Open(file_mag.get(f).get())
    if _shp is None:
        raise Exception('failed to open file (%s)' % f)

    _lyr = _shp.GetLayer(layer_name) if layer_name else _shp.GetLayer()

    if ext:
        _ext = ext.project_to(_lyr.GetSpatialRef())
        if _ext is None:
            logging.warning('failed to reproject the query extent')
            return
        _lyr.SetSpatialFilter(_ext.poly)

    for _r in _lyr:
        if _r is None:
            continue
            
        _g = _r.geometry()
        if _g is None:
            continue

        _p = geo_polygon(_g.Clone())
        _s = _r.items()
        _s['FID'] = _r.GetFID()

        yield _p, _s

    del _lyr, _shp
