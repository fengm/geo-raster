#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: visualize_bands.py
Author: Min Feng
Version: 0.1
Create: 2014-04-03 16:40:03
Description: convert raster data to visualiable image
'''

import logging

def search_threshold(vs, ls, sh):
    _sum = int(sum(vs) * sh)

    _t = 0
    for i in range(len(vs)):
        _t += vs[i]
        if _t > _sum:
            return ls[i]

    raise Exception('failed to find threshold')

def convert_band_sr(bnd, row, line, ref, sh=0.2, met={}):
    import numpy as np

    if bnd.nodata == None:
        bnd.nodata = 0

    if row == 0 and line == bnd.height:
        _bnd = bnd.cache()
        if _bnd is None:
            return None
        _dat = _bnd.data
    else:
        _dat = bnd.read_rows(row, line)

    if _dat is None:
        return None

    _base = 10

    import math
    from gio import config

    _min = config.getfloat('conf', 'sr_min', 500)
    _max = config.getfloat('conf', 'sr_max', 4500)

    _low = math.log(_min, _base)
    _top = math.log(_max, _base)

    _dat[_dat > (_max - _min)] = (_max - _min)
    _dat[_dat < _min] = _min

    _ddd = np.zeros(_dat.shape, dtype=np.uint8)
    _ddd[_dat > _min] = (np.log10(_dat.astype(np.float32)[_dat > _min]) - _low) * (256.0 / (_top - _low))

    return _ddd

def convert_band(bnd, row, line, ref, sh=0.2, met={}):
    import numpy as np

    if bnd.nodata == None:
        bnd.nodata = 0

    # _bnd = bnd.cache()
    bnd.read_rows(row, line)

    _dat = bnd.cached.data_ma
    _ddd = _dat

    if met.get('scale', None) == None:
        _min = _dat.min()
        _max = _dat.max()

        _bin = int(_max - _min)
        _bin = max(_bin, 10)

        logging.info('data range: %s, %s, %s' % (_min, _max, _bin))
        _vs, _ls = np.histogram(_ddd, bins=_bin, range=(_min, _max))

        _low = search_threshold(_vs, _ls, sh)
        _top = search_threshold(_vs[::-1], _ls[::-1], sh)

        met['scale'] = [_low, _top]
    else:
        _low = met['scale'][0]
        _top = met['scale'][1]

    if _top <= _low:
        raise Exception('failed to find threshold %s - %s' % (_low, _top))

    logging.info('threshold: %s - %s' % (_low, _top))

    _dat = (_dat.astype(np.float32) - _low) * (256.0 / (_top - _low))

    _dat[_dat > 255] = 255
    _dat[_dat < 0] = 0

    return _dat
    # return bnd.from_ma_grid(_dat, nodata=0)

def get_band_hdf(img, b):
    import re

    _bs = {}
    for _b, _k in img.sub_datasets():
        _m = re.search('B(\d)0', _k) or re.search('band(\d)', _k)
        if _m:
            _bs[int(_m.group(1))] = _b

    return img.get_subdataset(_bs[int(b)])

def visualize_bands(f_inp, bands, compress, convert_sr, f_out, fzip):
    from gio import geo_raster as ge
    import os

    print('loading', f_inp)

    _bnds = []
    if '{}' in f_inp:
        for _b in bands:
            _bnds.append(ge.open(fzip.unzip(f_inp.format(_b))).get_band())
    elif f_inp.endswith('.tar.gz'):
        print('processing tar.gz')
        import tarfile
        import re

        _t = tarfile.open(f_inp)

        _bs = {}
        for _l in _t.getmembers():
            _m = re.search('_b(\d+)\.tif', _l.name.lower())
            if _m:
                _bs[_m.group(1)] = _l

        _d_tmp = fzip.generate_file()
        os.makedirs(_d_tmp)

        _fs = []
        for _b in bands:
            _fs.append(_bs[_b])

        _t.extractall(_d_tmp, _fs)

        for _b in _fs:
            _bnds.append(ge.open(os.path.join(_d_tmp, _b.name)).get_band())
    else:
        _f_in = fzip.unzip(f_inp)

        _hdr = os.path.splitext(f_inp)[0] + '.hdr.gz'
        if os.path.exists(_hdr):
            fzip.unzip(_hdr)

        if _f_in.endswith('hdf'):
            _img = ge.geo_raster.open(_f_in)

            for _b in bands:
                _bnds.append(get_band_hdf(_img, _b).get_band())
        else:
            _img = ge.geo_raster.open(_f_in)
            for _b in bands:
                _bnds.append(_img.get_band(int(_b)))

    if len(_bnds) not in [1, 3]:
        raise Exception('Incorrect band numbers %s' % len(_bnds))

    _bnd = _bnds[0]

    _opt = []
    if compress:
        if f_out.endswith('.tif'):
            # _opt.append('compress=lzw')
            _opt.append('compress=jpeg')
            _opt.append('tiled=yes')
            _opt.append('predictor=2')
        if f_out.endswith('.img'):
            _opt.append('COMPRESS=YES')

    _img = ge.geo_raster.create(f_out, [len(_bnds), _bnd.height, _bnd.width],
            _bnd.geo_transform, _bnd.proj, ge.pixel_type(), opts=_opt)

    _met = {}
    if convert_sr == 'sr':
        # _line = 5024
        _line = _bnd.height
        for i in range(len(_bnds)):
            print(' + band', bands[i], 'sr' if convert_sr else 'dn')

            _bbb = _img.get_band(i + 1)
            _fun = convert_band_sr if convert_sr else convert_band

            from gio import progress_percentage
            _ppp = progress_percentage.progress_percentage(_bnd.height)

            for _row in range(0, _bnd.height, _line):
                _ppp.next(_line)

                _dat = _fun(_bnds[i], _row, _line, _bnd, 0.2, _met)
                if _dat is None:
                    continue

                _bbb.write(_dat, 0, _row)

            _ppp.done()
    else:
        for i in range(len(_bnds)):
            print(' + band', bands[i], 'sr' if convert_sr else 'dn')

            _bbb = _img.get_band(i + 1)
            _fun = convert_band_sr if convert_sr else convert_band
            _bbb.write(_fun(_bnds[i], 0, _bbb.height, _bnd, 0.2, _met), 0, 0)

    _img = None

def main(opts):
    import os
    from gio import file_unzip, config
    
    with file_unzip.file_unzip() as _zip:
        _f_inp = config.get('conf', 'input')
        _f_out = opts.output

        if os.path.isdir(_f_out):
            from gio import landsat
            _f_out = os.path.join(_f_out, '%s_%s_%s.tif' % (landsat.parse(os.path.basename(_f_inp)),
                'sr' if opts.convert_sr else 'dn',
                ''.join(map(str, opts.bands))
                ))

        _d_tmp = _zip.generate_file()
        os.makedirs(_d_tmp)

        visualize_bands(_f_inp, opts.bands, opts.compress, opts.convert_sr,
                os.path.join(_d_tmp, os.path.basename(_f_out)), _zip)

        file_unzip.compress_folder(_d_tmp, os.path.dirname(os.path.abspath(_f_out)), [])

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-b', '--bands', dest='bands', required=True, nargs='+')
    _p.add_argument('-o', '--output', dest='output', required=True)
    _p.add_argument('-sr', '--convert-sr', dest='convert_sr', action='store_true')
    _p.add_argument('-c', '--compress', dest='compress', action="store_true")
    _p.add_argument('--sr-min', dest='sr_min', type=float, default=500)
    _p.add_argument('--sr-max', dest='sr_max', type=float, default=4500)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])


