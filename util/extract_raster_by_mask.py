#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: extract_region.py
Author: Min Feng
Version: 0.1
Create: 2018-01-04 16:53:27
Description:
'''

def _wrs2(t, fzip):
    import os

    _f_shp = os.environ['D_DATA_WRS2']
    _f_tmp = fzip.generate_file('', '.shp')
    _cnd = '-where "PATHROW=\'%s\'"' % t
    _cmd = 'ogr2ogr %s %s %s' % (_cnd, _f_tmp, _f_shp)

    from gio import run_commands
    run_commands.run(_cmd)
    return _f_tmp
    
def _mask(f, fzip):
    from gio import geo_base as gb
    from gio import rasterize_band as rb
    from gio import file_mag
    from gio import config

    _ce = config.getfloat('conf', 'cell_size', 30.0)
    _gs = [_g for _g, _ in gb.load_shp(file_mag.get(f).get())]

    if len(_gs) == 0:
        raise Exception('no valid region provided')

    if _gs[0].proj.IsGeographic():
        _ce = _ce / 120000

    _msk = rb.to_mask(rb.to_raster(_gs, _ce), _gs)
    _f_msk = fzip.generate_file('', '.tif')

    fzip.save(_msk, _f_msk)
    return _f_msk

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
    from gio import file_unzip

    _clr = None if not opts.color else ge.load_colortable(opts.color)
    _bnd = None

    _inp = opts.input
    if len(_inp) > 1:
        _bnd = gx.geo_band_stack_zip.from_list(_inp)
        print(_bnd, len(_inp))
    else:
        if _inp[0].endswith('.shp'):
            _bnd = gx.geo_band_stack_zip.from_shapefile(_inp[0])
        elif _inp[0].endswith('.txt'):
            with open(_inp[0]) as _fi:
                _fs = _fi.read().strip().splitlines()
                if not _fs:
                    return
                _bnd = gx.geo_band_stack_zip.from_list(_fs)
        else:
            _bnd = ge.open(_inp[0]).get_band()
            
    with file_unzip.zip() as _zip:
        _f_msk = opts.mask
        if _f_msk.endswith('.shp'):
            _f_msk = _mask(opts.mask, _zip)
            
        _mak = ge.open(_f_msk).get_band().cache()
        _bnd = _bnd.read_block(_mak)
    
        if not opts.keep_pixels:
            _bnd.data[_mak.data != 1] = _bnd.nodata
    
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
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True, nargs='+')
    _p.add_argument('-r', '-m', '--mask', dest='mask', required=True)
    _p.add_argument('-k', '--keep-pixels', dest='keep_pixels', type='bool', default=False)
    _p.add_argument('-c', '--color', dest='color')
    _p.add_argument('--cell-size', dest='cell_size', type=float)
    _p.add_argument('-o', '--output', dest='output', required=True)
    _p.add_argument('-e', '--exclude-noises', dest='exclude_noises', type=int, default=0)
    _p.add_argument('--cache', dest='cache')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

