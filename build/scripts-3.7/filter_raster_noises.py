#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: filter_raster_noises.py
Author: Min Feng
Version: 0.1
Create: 2018-02-12 18:05:06
Description: reduce noises in a raster file
'''

def filter_noise(bnd, s):
    from gio import mod_filter
    from gio import stat_band
    import logging

    _ss = stat_band.stat(bnd)
    _vs = [_v for _v in list(_ss.keys()) if _v != bnd.nodata]

    print('values:', sorted(_vs))

    if len(_vs) <= 0:
        return

    _nodata = bnd.nodata
    bnd.nodata = 300

    if True:
        logging.debug('expend pixels')

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
    for _i in range(5):
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
    from gio import config

    _clr = None if not opts.color else ge.load_colortable(opts.color)
    _bnd = ge.open(opts.input).get_band().cache()

    if opts.exclude_noises < 0:
        raise Exception('wrong parameter')

    print('exclude noises (%s)' % opts.exclude_noises)
    if _bnd.pixel_type != ge.pixel_type():
        raise Exception('only exclude noises for byte type raster')

    if opts.mmu:
        filter_noise(_bnd, opts.exclude_noises)
    else:
        from gio import mod_filter
        mod_filter.filter_band_median(_bnd, config.getint('conf', 'exclude_noises'), \
                config.getint('conf', 'iteration'))

    _clr = _clr if _clr else _bnd.color_table

    from gio import file_unzip
    import os
    with file_unzip.file_unzip() as _zip:
        _d_tmp = _zip.generate_file()
        _f_tmp = os.path.join(_d_tmp, os.path.basename(opts.output))

        os.makedirs(_d_tmp)
        _bnd.save(_f_tmp, color_table=_clr)

        file_unzip.compress_folder(_d_tmp, os.path.dirname(os.path.abspath(opts.output)), [])

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-c', '--color', dest='color')
    _p.add_argument('-o', '--output', dest='output', required=True)
    _p.add_argument('-e', '--exclude-noises', dest='exclude_noises', type=int, default=1)
    _p.add_argument('-m', '--mmu', dest='mmu', action='store_true', default=False)
    _p.add_argument('-t', '--iteration', dest='iteration', default=1, type=int)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

