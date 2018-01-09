'''
File: global_task.py
Author: Min Feng
Version: 0.1
Create: 2016-06-17 10:33:01
Description: prepare and run the processes to process global data
'''

import logging

def load_shp(f, column=None, ext=None, proj=None):
    from osgeo import ogr
    import geo_base as gb

    logging.info('loading the input shapefile')

    _shp = ogr.Open(f)
    if _shp == None:
        raise Exception('Failed to load shapefile ' + f)

    _lyr = _shp.GetLayer()
    if ext:
        _lyr.SetSpatialFilter(ext.project_to(_lyr.GetSpatialRef()).poly)

    if _lyr.GetGeomType() != 3:
        raise Exception('the input boundary file needs to be polygon type (%s)' % _lyr.GetGeomType())

    _objs = []
    _area = None

    _prj = proj or gb.modis_projection()
    for _f in _lyr:
        _g = _f.geometry()
        if _g is None:
            continue

        _obj = gb.geo_polygon(_g.Clone())
        _ext = _obj.extent()

        _ooo = _obj.project_to(_prj)
        logging.debug('loading %s from %s (%s)' % (column, _f, ', '.join(_f.keys())))

        _objs.append((_f[column] if column else _f.GetFID(), _ooo.extent(), _ooo))

        if _area == None:
            _area = _ext
        else:
            _area = _area.union(_ext)

    if len(_objs) == 0 or _area == None:
        return None, []

    _reg = _area.to_polygon().segment_ratio(30).project_to(_prj)
    return _reg.extent(), _objs

def files(bnd, objs):
    _ext = bnd.extent()
    _pol = _ext.to_polygon()

    if len(objs) > 0:
        _obj = objs[0][2]

        _pol = _pol.project_to(_obj.proj)
        _ext = _pol.extent()

    _fs = []
    for _f, _e, _p in objs:
        if not _e.is_intersect(_ext):
            continue

        if _pol.is_intersect(_p):
            _fs.append(_f)
    return _fs

class tiles:

    def __init__(self, image_size, cell_size, edge, proj=None):
        import math
        import geo_base as gb

        self.b = 6371007.181 #6378137.0
        self.s = image_size
        self.c = cell_size
        self.p = self.b * math.pi
        self.edge = edge

        self.proj = proj if proj else gb.modis_projection()

    def list(self, ext=None):
        import geo_base as gb

        _rows = int(2 * self.p / (self.s * self.c))
        _cols = int(2 * self.p / (self.s * self.c))

        _y = self.p / 2

        import progress_percentage
        _ppp = progress_percentage.progress_percentage(_rows, title='checking tiles')

        for _row in xrange(_rows):
            _ppp.next()
            _x = -self.p
            for _col in xrange(_cols):
                _ext = gb.geo_extent(_x, _y, _x + ((self.s + self.edge) * self.c), _y \
                        - ((self.s + self.edge) * self.c), self.proj)
                if ext == None or _ext.is_intersect(ext):
                    yield _col, _row

                _x += self.c * self.s
            _y -= self.c * self.s

        _ppp.done()

    def extent(self, col, row):
        _geo = [-self.p + (col * self.s * self.c), self.c, 0, self.p / 2 - (row * self.s * self.c), 0, -self.c]

        import geo_raster as ge
        return ge.geo_raster_info(_geo, self.s+self.edge, self.s+self.edge, self.proj)

    def files(self, bnd, objs):
        return files(bnd, objs)

class tile:

    def __init__(self, image_size, cell_size, col, row, fs, ps=None, edge=1, proj=None):
        self.image_size = image_size
        self.cell_size = cell_size
        self.col = col
        self.row = row
        self.files = fs
        self.params = ps
        self.tag = 'h%03dv%03d' % (col, row)
        self.edge = edge
        self.proj = None

        if proj is not None:
            if isinstance(proj, str):
                self.proj = proj
            else:
                self.proj = proj.ExportToProj4()

    def proj_obj(self):
        from gio import geo_base as gb
        return gb.proj_from_proj4(self.proj)

    def extent(self):
        return tiles(self.image_size, self.cell_size, self.edge, self.proj_obj()).extent(self.col, self.row)

    def obj(self):
        return {
                'image_size': self.image_size,
                'cell_size': self.cell_size,
                'col': self.col,
                'row': self.row,
                'files': self.files,
                'params': self.params,
                'tag': self.tag,
                'edge': self.edge,
                'proj': self.proj
                }

    def filter_files(self, f, column='file'):
        _ext = self.extent()

        _reg, _objs = load_shp(f, column, _ext.extent().to_polygon(), proj=self.proj_obj())
        if _reg == None:
            return []

        return files(_ext, _objs)

    @staticmethod
    def from_obj(obj):
        _t_proj = obj.get('proj', None)
        _t_edge = obj.get('edge', 1)

        # from gio import geo_base as gb
        # _proj = gb.proj_from_proj4(str(_t_proj)) if _t_proj else None

        return tile(obj['image_size'], obj['cell_size'], obj['col'],
                obj['row'], obj['files'], obj['params'], _t_edge, str(_t_proj) if _t_proj else _t_proj)

def _output_geometries(geos, proj, geo_type, f_shp):
    from osgeo import ogr
    import os

    logging.debug('output shapefile to ' + f_shp)
    _drv_type = 'ESRI Shapefile'
    if f_shp.lower().endswith('.kml'):
        _drv_type = 'KML'

    _drv = ogr.GetDriverByName(_drv_type)
    if os.path.exists(f_shp):
        _drv.DeleteDataSource(f_shp)

    _shp = _drv.CreateDataSource(f_shp)
    _lyr = _shp.CreateLayer(f_shp[:-4], proj, geo_type)

    _fld = ogr.FieldDefn('tag', ogr.OFTString)
    _fld.SetWidth(max([len(_geo[1]) for _geo in geos]))

    _lyr.CreateField(_fld)

    for _geo, _tag in geos:
        _fea = ogr.Feature(_lyr.GetLayerDefn())
        _fea.SetGeometry(_geo.poly)
        _fea.SetField('tag', _tag)
        _lyr.CreateFeature(_fea)
        _fea.Destroy()

def _output_polygons(polys, f_shp):
    from osgeo import ogr
    if len(polys) == 0: return
    logging.debug('output polygon to ' + str(f_shp))

    from gio import file_unzip
    with file_unzip.file_unzip() as _zip:
        _f_tmp = _zip.generate_file('', '.shp')
        _output_geometries(polys, polys[0][0].proj, ogr.wkbPolygon, _f_tmp)

        f_shp.put(_f_tmp)

def make(f_inp, column=None, image_size=1000, cell_size=30, ps=None, f_shp=None, edge=1, proj=None):
    from gio import geo_base as gb

    _proj = proj or gb.modis_projection()
    _ext, _objs = load_shp(file_obj(f_inp).get(), column, proj=_proj)

    if _ext == None:
        return []

    _tils = tiles(image_size, cell_size, edge, _proj)

    logging.info('detected extent %s' % str(_ext))

    _pp = []
    _ps = []

    for _col, _row in _tils.list(_ext):
        _bnd = _tils.extent(_col, _row)

        _fs = _tils.files(_bnd, _objs)
        if len(_fs) == 0:
            continue

        _tile = tile(image_size, cell_size, _col, _row, _fs, ps, edge, _proj)
        _ps.append(_tile)

        if f_shp:
            _pp.append((_bnd.extent().to_polygon(), _tile.tag))

    if f_shp:
        _output_polygons(_pp, file_obj(f_shp))

    # _pps = [_g[2] for _g in _objs]
    # gb.output_polygons(_pps, f_shp[:-4] + '_test.shp')

    return _ps

def file_obj(f):
    from gio import file_mag
    return file_mag.get(f) if isinstance(f, str) else f

def save(rs, f_out):
    _f_out = file_obj(f_out)

    _rs = [_r.obj() for _r in rs]

    from gio import file_unzip

    with file_unzip.file_unzip() as _zip:
        _f_tmp = _zip.generate_file('', '.txt')

        import json
        with open(_f_tmp, 'wb') as _f:
            json.dump(_rs, _f)

        _f_out.put(_f_tmp)

def load(f_inp):
    import json

    with open(file_obj(f_inp).get(), 'rb') as _f:
        _rs = json.load(_f)
        return [tile.from_obj(_r) for _r in _rs]

