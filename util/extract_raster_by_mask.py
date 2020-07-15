#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: extract_region.py
Author: Min Feng
Version: 0.1
Create: 2018-01-04 16:53:27
Description:
'''

def filter_noise(bnd, s):
    from gio import mod_filter
    import logging

    _nodata = bnd.nodata
    bnd.nodata = 300

    if False:
        logging.debug('expend pixels')

        _vs = list(range(50))
        _bv = 255

        _dat = bnd.data
        for _v in _vs:
            for _i in range(3):
                _num = mod_filter.expand(_dat, \
                        _dat != bnd.nodata,\
                        _v, _bv, 2, 20)
                logging.debug('filtered %s %s pixels' % (_i, _num))
                if _num < 10:
                    break

        for _v in _vs:
            for _i in range(3):
                _num = mod_filter.expand(_dat, \
                        _dat != bnd.nodata,\
                        _v, _bv, 1, 5)
                logging.info('filtered %s %s pixels' % (_i, _num))
                if _num < 10:
                    break

    logging.debug('filter noise (dis: %s, num: %s)' % (4, 10))
    for _i in range(10):
        _min = 5 * s
        _num = mod_filter.clean(bnd, 4, _min)

        logging.debug('filtered %s %s pixels' % (_i, _num))
        if _num < 30:
            break

    for _i in range(5):
        _num = mod_filter.clean(bnd, 1, s)
        logging.debug('filtered %s %s pixels' % (_i, _num))
        if _num < 20:
            break

    bnd.nodata = _nodata

def main(opts):
    from gio import geo_raster as ge
    from gio import geo_raster_ex as gx

    _clr = None if not opts.color else ge.load_colortable(opts.color)
    _bnd = None

    if opts.input.endswith('.shp'):
        _bnd = gx.geo_band_stack_zip.from_shapefile(opts.input)
    else:
        _bnd = ge.open(opts.input).get_band()

    _mak = ge.open(opts.mask).get_band().cache()
    _val = 0

    if _mak.nodata is not None:
        _val = _mak.nodata

    _bnd = _bnd.read_block(_mak)
    _bnd.data[_mak.data == _val] = _bnd.nodata

    if opts.exclude_noises > 0:
        print('exclude noises (%s)' % opts.exclude_noises)

        if _bnd.pixel_type != ge.pixel_type():
            raise Exception('only exclude noises for byte type raster')

        filter_noise(_bnd, opts.exclude_noises)

    _clr = _clr if _clr else _bnd.color_table

    from gio import file_unzip
    import os
    with file_unzip.zip() as _zip:
        _bnd.color_table = _clr
        _zip.save(_bnd, opts.output)

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-m', '--mask', dest='mask', required=True)
    _p.add_argument('-c', '--color', dest='color')
    _p.add_argument('-o', '--output', dest='output', required=True)
    _p.add_argument('-e', '--exclude-noises', dest='exclude_noises', type=int, default=0)
    _p.add_argument('--cache', dest='cache')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

