#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: upload_data_s3.py
Author: Min Feng
Version: 0.1
Create: 2018-02-27 13:25:48
Description:
'''

def output_shp(f_inp, b, d_out, f_out, ext):
    from osgeo import ogr
    from gio import file_mag
    import os

    _inp = ogr.Open(file_mag.get(f_inp).get())
    _yyy = _inp.GetLayer()

    if ext:
        print('extent file', ext)
        
        from gio import geo_raster as ge
        if isinstance(ext, ge.geo_raster_info):
            _ext = ext.extent().to_polygon().segment_ratio(10)
        else:
            _ext = load_exts(ext)

        _yyy.SetSpatialFilter(_ext.project_to(_yyy.GetSpatialRef()).poly)

    _drv = ogr.GetDriverByName('ESRI Shapefile')
    os.path.exists(f_out) and _drv.DeleteDataSource(f_out)

    _shp = _drv.CreateDataSource(f_out)
    _nam = os.path.basename(f_out)
    _lyr = _shp.CreateLayer(os.path.basename(_nam)[:-4] if _nam.lower().endswith('.shp') else _nam, _yyy.GetSpatialRef(), ogr.wkbPolygon)

    _fld = ogr.FieldDefn('FILE', ogr.OFTString)
    _fld.SetWidth(254)
    _lyr.CreateField(_fld)

    _fld = ogr.FieldDefn('TAG', ogr.OFTString)
    _fld.SetWidth(25)
    _lyr.CreateField(_fld)

    for _r in _yyy:
        _ftr = ogr.Feature(_lyr.GetLayerDefn())

        _vs = _r.items()
        _f = update_path(_vs['FILE'], b, d_out)

        _ftr.SetField('file', _f)

        if 'TAG' in _vs:
            _ftr.SetField('tag', _vs['TAG'])

        _ftr.SetGeometry(_r.geometry())
        _lyr.CreateFeature(_ftr)
        _ftr.Destroy()

def update_path(p, b, d_out):
    from gio import file_mag
    _p = file_mag.get(p).get()
    
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

def upload_file(f, b, d_out):
    from gio import file_mag
    
    _out = update_path(f, b, d_out)
    _key = file_mag.get(_out)
    
    import logging
    logging.info('uploading file %s %s' % (f, _out))
    
    if not _key.exists():
        _key.put(file_mag.get(f).get())
        
    return _out
    
def load_exts(f):
    from osgeo import ogr
    from gio import geo_base as gb

    _inp = ogr.Open(f)
    _yyy = _inp.GetLayer()
    
    for _r in _yyy:
        _g = gb.geo_polygon(_r.geometry().Clone())
        return _g

    return None

def load_list(f, b, d_out, ext):
    from osgeo import ogr
    from gio import file_mag

    _f = file_mag.get(f).get()
    print('loading', _f)
    
    _inp = ogr.Open(_f)
    _yyy = _inp.GetLayer()
    
    if ext:
        print('extent file', ext)
        
        from gio import geo_raster as ge
        if isinstance(ext, ge.geo_raster_info):
            _ext = ext.extent().to_polygon().segment_ratio(10)
        else:
            _ext = load_exts(ext)

        _yyy.SetSpatialFilter(_ext.project_to(_yyy.GetSpatialRef()).poly)

    _ls = []
    for _r in _yyy:
        _f = _r.items()['FILE']
        # _o = update_path(_f, b, d_out)
        # print _f, '|', _o

        # _ls.append((_f, _o))
        # if not file_mag.get(_f).exists():
        #     _f = None
            
        _ls.append((_f, b, d_out))

    return _ls

def main(opts):
    from gio import multi_task
    import os

    _ps = []
    _s = 0.0
    for _f, _b, _d_out in multi_task.load(load_list(opts.input, opts.base_path, \
            (opts.output + ('data' if opts.output.endswith('/') else '/data')), opts.extent), opts):

        if not _f:
            continue
        
        # if not os.path.exists(_f):
        #     continue

        # _s += os.path.getsize(_f) / (1024.0 * 1024.0 * 1024.0)
        # if _f_out.endswith('.gz'):
        #     _f_out = _f_out[:-3]

        _ps.append((_f, _b, _d_out))
        
    for _i in range(min(len(_ps), 3)):
        print('...', _ps[_i])

    print('size', '%0.3fGb' % _s)
    _rs = multi_task.run(upload_file, _ps, opts)
    del _rs

    from gio import file_unzip
    with file_unzip.file_unzip() as _zip:
        _d_tmp = _zip.generate_file()
        os.makedirs(_d_tmp)

        output_shp(opts.input, opts.base_path, opts.output + '/data', os.path.join(_d_tmp, 'list.shp'), opts.extent)
        file_unzip.compress_folder(_d_tmp, opts.output, [])

    print('done')

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-e', '--extent', dest='extent')
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

