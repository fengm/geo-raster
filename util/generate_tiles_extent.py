#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: generate_tiles_extent.py
Author: Min Feng
Version: 0.1
Create: 2018-01-09 01:46:17
Description:
'''

def check_image(f):
    from gio import geo_raster as ge
    import os

    try:
        _f = f.get()
        if (not _f) or not os.path.exists(_f):
            return 0
        ge.open(_f).get_band().cache()

        return 1
    except KeyboardInterrupt as _err:
        print('\n\n* User stopped the program')
        raise _err
    except Exception:
        pass

        # import logging
        # import traceback

        # logging.error(traceback.format_exc())
        # logging.error(str(err))

    return 0

def _task(tile, u, image_check=False):
    from gio import file_mag
    # if tile.col != 1156:
    #     return
    # if tile.row != 970:
    #     return

    _f = u % {'col': 'h%03d' % tile.col, 'row': 'v%03d' % tile.row}
    _o = file_mag.get(_f)

    if _o.exists():
        return (tile, _f, check_image(_o) if image_check else 2)
    
    import logging
    logging.info('failed to find %s' % _f)

    return None

def _format_url(inp, f):
    import re

    _f = f
    if '/' not in _f and '\\' not in _f:
        _t = _f
        if _t.startswith('_'):
            _t = _t[1:]

        import os
        _f = os.path.join(inp, 'data/h001/v001/h001v001/h001v001_%s' % (_t))

    _f = re.sub('h\d\d\d+', '%(col)s', _f)
    _f = re.sub('v\d\d\d+', '%(row)s', _f)

    return _f

def _get_tag(f):
    import re

    _m = re.search('h\d+v\d+', f)
    if _m:
        return _m.group()

    _m = re.search('p\d+r\d+', f)
    if _m:
        return _m.group()

    return ''

def generate_shp(rs, ts, f_out):
    from gio import geo_base as gb
    from osgeo import ogr
    from gio import progress_percentage
    import os

    if not os.path.exists(os.path.dirname(f_out)):
        os.makedirs(os.path.dirname(f_out))

    _drv = ogr.GetDriverByName('ESRI Shapefile')
    
    _tag = os.path.basename(f_out)[:-4]
    os.path.exists(_tag) and _drv.DeleteDataSource(_tag)
    
    _shp = _drv.CreateDataSource(f_out)
    _lyr = _shp.CreateLayer(_tag, ts[0].proj_obj(), ogr.wkbPolygon)

    _fld = ogr.FieldDefn('FILE', ogr.OFTString)
    _fld.SetWidth(254)
    _lyr.CreateField(_fld)

    _fld = ogr.FieldDefn('TAG', ogr.OFTString)
    _fld.SetWidth(25)
    _lyr.CreateField(_fld)

    _perc = progress_percentage.progress_percentage(len(rs))

    _fs = []
    _ts = 0
    _cs = []

    for _r in rs:
        _perc.next()

        if _r is None:
            continue

        _t, _f, _c = _r
        if not _c:
            _cs.append(_f)
            continue

        _ftr = ogr.Feature(_lyr.GetLayerDefn())
        _ftr.SetField('file', _f)
        _ftr.SetField('tag', _get_tag(_f))
        _fs.append(_f)

        _ftr.SetGeometry(_t.extent().extent().to_polygon().poly)
        _lyr.CreateFeature(_ftr)
        _ftr.Destroy()

        _ts += 1

    _perc.done()

    with open(f_out[:-4] + '.txt', 'w') as _fo:
        _fo.write('\n'.join(_fs))

    return _ts, _cs

def main(opts):
    from gio import config
    from gio import file_mag
    import logging
    import os
    
    if file_mag.get(opts.output).exists() and not opts.over_write:
        logging.warning('skip processed %s' % opts.output)
        return
    
    _d_inp = config.get('conf', 'input')

    if not _d_inp.startswith('s3://'):
        _d_inp = os.path.abspath(_d_inp)

    _f_mak = file_mag.get(os.path.join(_d_inp, 'tasks.txt'))

    _u = _format_url(_d_inp, opts.ext)
    # if not _u.startswith('s3://'):
    #     _u = os.path.join(opts.input, _u)

    print('url:', _u)
    logging.info('url: %s' % _u)

    from gio import global_task
    if not _f_mak.exists():
        raise Exception('failed to find the tile file')

    _ts = global_task.load(_f_mak)

    from gio import multi_task
    _rs = multi_task.run(_task, [(_r, _u, opts.check_image) for _r in multi_task.load(_ts, opts)], opts)
    print('')

    from gio import file_unzip
    with file_unzip.file_unzip() as _zip:
        _d_tmp = _zip.generate_file()
        os.makedirs(_d_tmp)

        _nu, _cs = generate_shp(_rs, _ts, os.path.join(_d_tmp, os.path.basename(opts.output)))
        if _nu <= 0:
            raise Exception('no valid image was found')

        if len(_cs) > 0:
            print('found %s invalid files' % len(_cs))
            for _l in _cs:
                print(_l)
            return
            # raise Exception('found invalid images')

        logging.info('added %s file' % _nu)
        print('added %s file' % _nu)

        file_unzip.compress_folder(_d_tmp, os.path.dirname(opts.output), [])

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-c', '--cache', dest='cache')
    _p.add_argument('-f', '--format-url', dest='format_url', type='bool', default=True)
    _p.add_argument('--check-image', dest='check_image', action='store_true')
    _p.add_argument('--over-write', '--over-write', dest='over_write', action='store_true', default=False)
    _p.add_argument('-e', '--ext', dest='ext', required=True)
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

