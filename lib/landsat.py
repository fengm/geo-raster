'''Module for process Landsat file information'''

import re

band_vals = [1, 2, 3, 4, 5, 7]
band_txts = ['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2']
band_l_rate = [0.659553184, 0.66026684, 0.659565581, 0.660032494, 0.660078238, 0.660153937]
band_h_rate = [1.516177958, 1.514539182, 1.516149462, 1.515076923, 1.514971928, 1.514798206]
band_gain_low = [[-6.2, 293.7], [-6.4, 300.9], [-5.0, 234.4], [-5.1, 241.1], [-1.0, 47.57], [-0.35, 16.54]]
band_gain_high = [[-6.2, 191.6], [-6.4, 196.5], [-5.0, 152.9], [-5.1, 157.4], [-1.0, 31.06], [-0.35, 10.80]]

class landsat_info:

    def __init__(self, sensor, tile, ac_date, full_name=None, note=None, mission=None):
        self.sensor = sensor.upper() if sensor else None
        self.tile = tile
        self.ac_date = ac_date
        self.full_name = full_name
        self.note = note
        self.mission = int(mission) if mission else None

        if self.sensor and len(self.sensor) == 1 and self.sensor.startswith('L'):
            if self.mission:
                if self.mission == 5:
                    self.sensor = 'LT'
                if self.mission == 7:
                    self.sensor = 'LE'

        if not self.mission and self.sensor:
            if self.sensor == 'LC':
                self.mission = 8
            if self.sensor == 'LE':
                self.mission = 7
            if self.sensor == 'LT' and int(self.ac_date[:4]) > 1993:
                self.mission = 5

        self.path = -1
        self.row = -1
        if tile:
            self.path = int(tile[1:4])
            self.row = int(tile[5:])

        import datetime
        self.ac_date_obj = datetime.datetime.strptime(ac_date, '%Y%m%d')

    def __str__(self):
        _cd = '%s%s' % (self.sensor if self.sensor else '', self.mission if self.mission else '')
        _id = [_cd] if _cd else []
        _id.extend([self.tile, self.ac_date])
        return '_'.join(_id)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, obj):
        return str(obj) == str(self)

    def __cmp__(self, obj):
        return cmp(str(self), str(obj))

class hls_info:

    def __init__(self, sensor, tile, ac_date, full_name=None, note=None, mission=None):
        self.sensor = sensor.upper() if sensor else None
        self.tile = tile
        self.ac_date = ac_date
        self.full_name = full_name
        self.note = note
        self.mission = int(mission) if mission else None

        import datetime
        self.ac_date_obj = datetime.datetime.strptime(ac_date, '%Y%m%d')

    def __str__(self):
        _cd = '%s%s' % (self.sensor if self.sensor else '', self.mission if self.mission else '')
        _id = [_cd] if _cd else []
        _id.extend([self.tile, self.ac_date])
        return '_'.join(_id)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, obj):
        return str(obj) == str(self)

    def __cmp__(self, obj):
        return cmp(str(self), str(obj))

def parse(code, file_only=False):
    if file_only:
        return _parse_item(code)

    return _parse_sid(code)

def _parse_item(code):
    _vs = parseLandsatId(code)
    if _vs is not None:
        return landsat_info(_vs[0], _vs[1], _vs[2], code, mission=_vs[3])

    _vs = parseHLSId(code)
    if _vs is not None:
        return hls_info(_vs[0], _vs[1], _vs[2], code, mission=_vs[3])

    return None

def _parse_sid(d):
    import os

    _id = _parse_item(d)
    if _id:
        return _id

    if os.path.isdir(d):
        for _root, _dirs, _files in os.walk(d):
            for _file in _files:
                _id = _parse_item(_file)
                if _id:
                    return _id

    return None

def band_to_text(b):
    if b not in band_vals:
        return ''

    return band_txts[band_vals.index(b)]

def parseLandsatId(id):
    _m = re.search('(L)(\d)(\w?)_(p\d{3}r\d{3})_(\d{8})', id)
    if _m:
        return _m.group(1) + _m.group(3), _m.group(4), _m.group(5), int(_m.group(2))

    _m = re.search('(L\w)(\d+)_L[^_]+_(\d{3})(\d{3})_(\d{8})', id)
    if _m:
        return _m.group(1), 'p%sr%s' % (_m.group(3), _m.group(4)), _m.group(5), int(_m.group(2))

    _m = re.search('(L\w)(\d{2})(\d{3})(\d{3})(\d{8})\d{2}T\d', id)
    if _m:
        return _m.group(1), 'p%sr%s' % (_m.group(3), _m.group(4)), _m.group(5), int(_m.group(2))

    _m = re.search('(p\d{3}r\d{3})_(\d)\w+(\d{8})', id)
    if _m:
        return '', _m.group(1), _m.group(3), '', int(_m.group(2))

    _m = re.search('[lL](\d)_(p\d{3}r\d{3})_(\d{8})', id)
    if _m:
        return 'L', _m.group(2), _m.group(3), int(_m.group(1))

    _m = re.search('(\w+)(\d)_(p\d{3}r\d{3})_(\d{8})', id)
    if _m:
        return _m.group(1), _m.group(3), _m.group(4), int(_m.group(2))

    _m = re.search('L(\d)\d?(\d{3})(\d{3})_\d{3}(\d{8})', id)
    if _m:
        return 'L', 'p%sr%s' % (_m.group(2), _m.group(3)), _m.group(4), int(_m.group(1))

    _m = re.search('(L\w)(\d)(\d{3})(\d{3})(\d{7})', id)
    if _m:
        import datetime
        _date = datetime.datetime.strptime(_m.group(5), '%Y%j')
        return _m.group(1), 'p%sr%s' % (_m.group(3), _m.group(4)), _date.strftime('%Y%m%d'), int(_m.group(2))

    _m = re.search('(\d)(\w?)_(p\d{3}r\d{3})_(\d{8})', id)
    if _m:
        return 'L' + _m.group(2), _m.group(3), _m.group(4), int(_m.group(1))

    _m = re.search('w2(p\d{3}r\d{3})_(\d{7})(\w{2})(\d)', id)
    if _m:
        import datetime
        _date = datetime.datetime.strptime(_m.group(2), '%Y%j')
        return _m.group(3), _m.group(1), _date.strftime('%Y%m%d'), int(_m.group(4))

    _m = re.search('w2(p\d{3}r\d{3})_(\d{7})L(\w{2})', id)
    if _m:
        import datetime
        _date = datetime.datetime.strptime(_m.group(2), '%Y%j')

        return _m.group(3), _m.group(1), _date.strftime('%Y%m%d'), None

    _m = re.search('(L\w)(\d)(\d{3})(\d{3})(\d{4})(\d{3})', id)
    if _m:
        _year = int(_m.group(4))
        _day = int(_m.group(5))

        if _year < 1900:
            _year += 2000
            if _year > 2900:
                _year -= 1000
            if _year > 2070:
                _year -= 100

        # _year += 2000
        # if _year > 2070:
        #     _year -= 100

        import datetime
        _date = datetime.datetime.strptime('%04d-%03d' % (_year, _day), '%Y-%j')

        return _m.group(1), 'p%sr%s' % (_m.group(3), _m.group(4)), _date.strftime('%Y%m%d'), _m.group(2)

    _m = re.search('(p\d{3}r\d{3})_(\d{8})', id)
    if _m:
        return None, _m.group(1), _m.group(2), None

    return None

def parseHLSId(sid):
    _m = re.search('HLS\.(\w\d{2})\.([^\.]+)\.(\d{7})\.', sid)
    if _m:
        import datetime
        _date = datetime.datetime.strptime(_m.group(3), '%Y%j')

        return _m.group(1), _m.group(2), _date.strftime('%Y%m%d'), None

    return None

def parseLandsatCode(id):
    _m = re.search('p\d{3}r\d{3}_\d+\w+\d{8}', id)
    if _m:
        return _m.group()

    _m = re.search('L\d\d?\d{3}\d{3}_\d{3}\d{8}', id)
    if _m:
        return _m.group()

    _m = re.search('L\w(\d)(\d{3})(\d{3})(\d{4})(\d{3})', id)
    if _m:
        return _m.group()

    return None

def getSensorName(d):
    if d >= 7:
        return 'ETM+'
    elif d >= 4:
        return 'TM'
    else:
        return 'MSS'

def normalizeId(sensor, pathrow, date):
    return 'L%s_%s_%s' % (sensor, pathrow, date)

def find_tiles(geom):
    '''return tiles at the given geometry'''

    from osgeo import ogr
    from . import config

    _f_shp = config.get('conf', 'wrs')
    _shp = ogr.Open(_f_shp)
    _lyr = _shp.GetLayer()

    import geo_base as gb
    _geom = None

    if geom != None:
        if isinstance(geom, ogr.Geometry):
            _geom = geom
        elif isinstance(geom, gb.geo_point):
            _geom = geom.to_geometry()
        elif isinstance(geom, gb.geo_polygon):
            _geom = geom.poly
        else:
            raise Exception('failed to parse the geometry')

        _lyr.SetSpatialFilter(_geom)

    _ps = []
    for _f in _lyr:
        _ps.append(_f['pathrow'])

    return _ps

def main():
    _f = '/export/data/bessie1/fengm/prog/vct/test1/w2p048r022_2002192LLE_sr'
    print(parse(_f))

def _init_env():
    import os, sys

    _dirs = ['lib', 'libs']
    _d_ins = [os.path.join(sys.path[0], _d) for _d in _dirs if \
            os.path.exists(os.path.join(sys.path[0], _d))]
    sys.path = [sys.path[0]] + _d_ins + sys.path[1:]

if __name__ == '__main__':
    _init_env()
    main()

