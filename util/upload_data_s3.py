#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: upload_data_s3.py
Author: Min Feng
Version: 0.1
Create: 2018-02-27 13:25:48
Description:
'''

def output_shp(f_inp, b, d_out, f_out):
    from osgeo import ogr
    import os

    _inp = ogr.Open(f_inp)
    _yyy = _inp.GetLayer()

    _drv = ogr.GetDriverByName('ESRI Shapefile')
    os.path.exists(f_out) and _drv.DeleteDataSource(f_out)

    _shp = _drv.CreateDataSource(f_out)
    _lyr = _shp.CreateLayer([x for x in os.path.basename(f_out)[:-4] if x[:-4] if x.lower().endswith('.shp') else x], _yyy.GetSpatialRef(), ogr.wkbPolygon)

    _fld = ogr.FieldDefn('FILE', ogr.OFTString)
    _fld.SetWidth(254)
    _lyr.CreateField(_fld)

    _fld = ogr.FieldDefn('TAG', ogr.OFTString)
    _fld.SetWidth(25)
    _lyr.CreateField(_fld)

    for _r in _yyy:
        _ftr = ogr.Feature(_lyr.GetLayerDefn())

        _vs = list(_r.items())
        _f = update_path(_vs['FILE'], b, d_out)

        _ftr.SetField('file', _f)

        if 'TAG' in _vs:
            _ftr.SetField('tag', _vs['TAG'])

        _ftr.SetGeometry(_r.geometry())
        _lyr.CreateFeature(_ftr)
        _ftr.Destroy()

def update_path(p, b, d_out):
    _p = p
    if b and p.startswith(b):
        _p = p[len(b):]
    else:
        import os
        _p = os.path.basename(_p)

    if _p.startswith('/'):
        _p = _p[1:]

    if _p.endswith('.gz'):
        _p = _p[:-3]

    return d_out + ('' if d_out.endswith('/') else '/') + _p

def compress_file(f, fzip):
    _f = f
    if f.endswith('.gz'):
        _f = fzip.unzip(_f)

    from gio import config
    if not config.getboolean('conf', 'compress'):
        return _f

    _f_tmp = fzip.generate_file('', '.tif')
    _cmd = 'gdalwarp -co compress=lzw -co tiled=yes %s %s' % (_f, _f_tmp)

    from gio import run_commands
    run_commands.run(_cmd)

    return _f_tmp

def upload_file(f, k):
    import boto
    import re
    from gio import config

    _mm = re.match('s3://([^/]+)/(.+)', k)
    if not _mm:
        raise Exception('failed to parse the output folder')

    _bucket = _mm.group(1)

    _s3 = boto.connect_s3(config.get('conf', 'access_key'), config.get('conf', 'opts.secret_key'))
    _bk = _s3.get_bucket(_bucket)

    _ff = _mm.group(2)
    _kk = _bk.get_key(_ff)
    if _kk is not None:
        return _ff

    _kk = _bk.new_key(_ff)

    from gio import file_unzip
    with file_unzip.file_unzip() as _zip:
        with open(compress_file(f, _zip), 'rb') as _fi:
            _kk.set_contents_from_file(_fi)

    return k

def load_list(f, b, d_out):
    from osgeo import ogr

    _inp = ogr.Open(f)
    _yyy = _inp.GetLayer()

    _ls = []
    for _r in _yyy:
        _f = list(_r.items())['FILE']
        _o = update_path(_f, b, d_out)

        _ls.append((_f, _o))

    return _ls

def main(opts):
    from gio import multi_task
    import os

    _ps = []
    _s = 0.0
    for _f, _f_out in multi_task.load(load_list(opts.input, opts.base_path, \
            (opts.output + '/data')), opts):
        if not os.path.exists(_f):
            continue

        _s += os.path.getsize(_f) / (1024.0 * 1024.0 * 1024.0)
        if _f_out.endswith('.gz'):
            _f_out = _f_out[:-3]

        _ps.append((_f, _f_out))

    for _i in range(min(len(_ps), 3)):
        print('...', _ps[_i])

    print('size', '%0.3fGb' % _s)
    _rs = multi_task.run(upload_file, _ps, opts)
    del _rs

    from gio import file_unzip
    with file_unzip.file_unzip() as _zip:
        _d_tmp = _zip.generate_file()
        os.makedirs(_d_tmp)

        output_shp(opts.input, opts.base_path, opts.output + '/data', os.path.join(_d_tmp, 'list.shp'))
        file_unzip.compress_folder(_d_tmp, opts.output, [])

    print('done')

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-ak', '--access-key', dest='access_key', default=None)
    _p.add_argument('-sk', '--secret-key', dest='secret_key', default=None)
    _p.add_argument('-p', '--base-path', dest='base_path')
    _p.add_argument('-c', '--compress', dest='compress', type='bool')
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

