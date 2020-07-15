'''
File: landsat_dataset.py
Author: Min Feng
Version: 0.1
Create: 2016-03-24 11:45:03
Description:
'''

import logging

class qa:

    qa_land = 1
    qa_shadow = 2
    qa_cloud = 3
    qa_water = 4
    qa_snow = 5
    qa_nodata = 255

    cf0_land = 1
    cf0_water = 5
    cf0_shadow = 3
    cf0_snow = 4
    cf0_cloud = 2
    cf0_nodata = 255

    cf1_land = 0
    cf1_water = 1
    cf1_shadow = 2
    cf1_snow = 3
    cf1_cloud = 4
    cf1_nodata = 255

    def __init__(self):
        pass

    @staticmethod
    def from_fmask(bnd, code_set):
        import numpy as np

        _dat = np.empty((bnd.height, bnd.width), dtype=np.uint8)
        _dat.fill(qa.qa_nodata)

        if code_set == 1:
            _dat[bnd.data == qa.cf1_land] = qa.qa_land
            _dat[bnd.data == qa.cf1_shadow] = qa.qa_shadow
            _dat[bnd.data == qa.cf1_cloud] = qa.qa_cloud
            _dat[bnd.data == qa.cf1_water] = qa.qa_water
            _dat[bnd.data == qa.cf1_snow] = qa.qa_snow
            _dat[bnd.data == qa.cf1_nodata] = qa.qa_nodata
        else:
            _dat[bnd.data == qa.cf0_land] = qa.qa_land
            _dat[bnd.data == qa.cf0_shadow] = qa.qa_shadow
            _dat[bnd.data == qa.cf0_cloud] = qa.qa_cloud
            _dat[bnd.data == qa.cf0_water] = qa.qa_water
            _dat[bnd.data == qa.cf0_snow] = qa.qa_snow
            _dat[bnd.data == qa.cf0_nodata] = qa.qa_nodata

        return bnd.from_grid(_dat, nodata=qa.qa_nodata)

class sr:
    def band(self, b):
        if b not in self._bs:
            raise Exception('failed to find band %s (%s)' % (b, str(self._bs)))

        logging.info('loading band %s' % (b))
        return self._load_band(b)

    def get_band(self, b):
        _b = self._band_no(self._inf, b)
        if _b not in self._bs:
            logging.error('failed to find band %s (%s) (%s)' % (b, _b, str(self._bs)))
            return None

        logging.info('loading TM band %s (%s)' % (b, _b))
        return self._load_band(_b)

    def get_cloud(self, b):
        return None

    def metadata(self):
        raise Exception('unsupported function')

    def tag(self):
        raise Exception('unsupported function')

    def _band_no_tm_lc(self, b):
        if b <= 5:
            return b + 1

        if b == 6:
            return 10

        if b == 7:
            return 7

        raise Exception('unsupported TM band num %s' % b)

    def _band_no_tm_etm(self, b):
        if b == 6:
            if b in self._bs:
                return b
            return 61

        return b

    def _band_no(self, inf, b):
        if inf.sensor.upper() == 'LC':
            return self._band_no_tm_lc(b)
        if inf.sensor.upper() == 'LE':
            return self._band_no_tm_etm(b)

        return b

class sr_dir(sr):

    def __init__(self, p, fzip):
        self._p = p

        from . import landsat
        self._inf = landsat.parse(p)
        if not self._inf:
            raise Exception('failed to parse %s' % p)

        import os
        if os.path.isdir(p):
            self._list_dir(p)
        else:
            raise Exception('not support the file %s' % p)

        self._fzip = fzip
        self._bnds = {}

    def _is_img(self, f):
        f = f.lower()
        return f.endswith('.img.gz') or f.endswith('.img') or f.endswith('.tif.gz') or f.endswith('.tif')

    def _list_dir(self, p):
        import os
        import re

        _fs = {}
        _bs = []
        for _f in os.listdir(p):
            _p = os.path.join(p, _f)
            _f = _f.lower()

            _m = self._is_img(_f) and re.search('sr_band(\d+)\.', _f)
            if _m:
                _fs['sr_b%s' % _m.group(1)] = _p
                _b = int(_m.group(1))
                if _b not in _bs:
                    _bs.append(_b)
                continue

            _m = self._is_img(_f) and (re.search('toa_band(\d+)\.', _f) or \
                    re.search('toa_b(\d+)\.', _f))
            if _m:
                _fs['toa_b%s' % _m.group(1)] = _p
                _b = int(_m.group(1))
                if _b not in _bs:
                    _bs.append(_b)
                continue

            _m = self._is_img(_f) and re.search('bt_band(\d+)\.', _f)
            if _m:
                _fs['toa_b%s' % _m.group(1)] = _p
                _b = int(_m.group(1))
                if _b not in _bs:
                    _bs.append(_b)
                continue

            _m = self._is_img(_f) and re.search('_cfmask\.', _f)
            if _m:
                _fs['cfmask'] = _p
                continue

            _m = (not _f.startswith('lnd')) and re.search('_mtl.txt', _f)
            if _m:
                _fs['mtl'] = _p
                continue

        self._fs = _fs
        self._bs = _bs
        
        logging.info('found bands: %s' % str(self._fs.keys()))
        assert 'mtl' in _fs

    def _load_band(self, b):
        from . import geo_raster as ge

        _b = b
        logging.info('loading band %s (%s)' % (b, _b))

        if _b not in list(self._bnds.keys()):
            _bn = ('sr_b%s' if 'sr_b%s' % _b in self._fs else 'toa_b%s') % _b
            logging.info('caching band %s' % _bn)

            self._bnds[_b] = ge.open(self._fzip.unzip(self._fs[_bn])).get_band()

        return self._bnds[_b]

    def get_cloud(self, code_set=0):
        _b = 'cloud'
        if _b in list(self._bnds.keys()):
            return self._bnds[_b]

        # if 'cloud' not in self._fs.keys():
        #     return None

        if _b in self._bs:
            from . import geo_raster as ge
            _bnd = ge.open(self._fzip.unzip(self._fs[_b])).get_band().cache()
            self._bnds['cloud'] = _bnd

            return _bnd

        _b = 'cfmask'
        if _b in self._fs:
            from . import geo_raster as ge
            _bnd = qa.from_fmask(ge.open(self._fzip.unzip(self._fs[_b])).get_band().cache(), code_set)
            self._bnds['cloud'] = _bnd

            return _bnd
            
        logging.warning('failed to find cfmask in (%s) (%s)' % \
                    (str(self._fs.keys()), str(self._bs)))
                    
        return None

    def tda_cloud(self, b):
        _bnd = b
        if _bnd == None:
            return None

        _dat = _bnd.data

        _idx_land = _dat == 0
        _idx_water = _dat == 1
        _idx_cloud_shadow = _dat == 2
        _idx_snow = _dat == 3
        _idx_cloud = _dat == 4

        import numpy as np
        _ddd = np.empty(_dat.shape, dtype=np.uint8)

        _ddd.fill(0)
        _ddd[_idx_land] = 1
        _ddd[_idx_water] = 5
        _ddd[_idx_cloud_shadow] = 2
        _ddd[_idx_cloud] = 3
        _ddd[_idx_snow] = 4

        return _bnd.from_grid(_ddd, nodata=255)

    def metadata(self):
        if 'mtl' not in list(self._fs.keys()):
            return None

        _ms = {}
        with open(self._fzip.unzip(self._fs['mtl'])) as _fi:
            for _l in _fi:
                _rs = [x.strip() for x in _l.strip().split('=')]
                if len(_rs) == 2:
                    _ms[_rs[0]] = _rs[1]

        if 'SUN_AZIMUTH' in _ms:
            _ms['SolarAzimuth'] = _ms['SUN_AZIMUTH']
        if 'SUN_ELEVATION' in _ms:
            _ms['SolarZenith'] = 1 - float(_ms['SUN_ELEVATION'])

        # if 'SolarAzimuth' not in _ms:
        #     print _ms.keys()
        assert('SolarAzimuth' in _ms)
        return _ms

    def tag(self):
        return 'dir'

class sr_hdf(sr):

    def __init__(self, f, fzip):
        if not f.endswith('.hdf'):
            raise Exception('only support HDF file')

        from . import landsat
        self._inf = landsat.parse(f)
        if not self._inf:
            raise Exception('failed to parse %s' % f)

        from . import geo_raster as ge
        import re

        _img = ge.open(f)

        _bs = []
        for _s, _d in _img.sub_datasets():
            _d = re.search('(\d+)$', _s)
            if _d:
                _bs = int(_d.group(1))

        self._img = _img
        self._bs = _bs
        self._f = f
        self._fzip = fzip

    def _load_band(self, b):
        return self._img.get_subdataset(b).get_band()

    def metadata(self):
        return self._img.raster.GetMetadata()

    def tag(self):
        return 'hdf'

def load(f, fzip):
    import os

    if os.path.isdir(f):
        return sr_dir(f, fzip)

    if f.endswith('.hdf.gz') or f.endswith('.hdf'):
        return sr_hdf(fzip.unzip(f), fzip)

    raise Exception('not support file %s' % f)

