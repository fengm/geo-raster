'''
File: generate_tiles_extent.py
Author: Min Feng
Version: 0.1
Create: 2018-01-09 01:46:17
Description:
'''

def _task(tile, opts):
    from gio import file_mag
    # if tile.col != 1156:
    #     return
    # if tile.row != 970:
    #     return

    _f = opts.ext % {'col': 'h%03d' % tile.col, 'row': 'v%03d' % tile.row}

    if file_mag.get(_f).exists():
        return (tile, _f)

    return None

def _get_tag(f):
    import re

    _m = re.search('h\d+v\d+', f)
    if _m:
        return _m.group()

    _m = re.search('p\d+r\d+', f)
    if _m:
        return _m.group()

    return ''

def generate_shp(rs, f_out):
    from gio import geo_base as gb
    from osgeo import ogr
    from gio.progress_percentage import progress_percentage
    import os

    if not os.path.exists(os.path.dirname(f_out)):
        os.makedirs(os.path.dirname(f_out))

    _drv = ogr.GetDriverByName('ESRI Shapefile')
    os.path.exists(f_out) and _drv.DeleteDataSource(f_out)
    _shp = _drv.CreateDataSource(f_out)
    _lyr = _shp.CreateLayer(filter(lambda x: x[:-4] if x.lower().endswith('.shp') else x, \
            os.path.basename(f_out)[:-4]), gb.modis_projection(), ogr.wkbPolygon)

    _fld = ogr.FieldDefn('FILE', ogr.OFTString)
    _fld.SetWidth(254)
    _lyr.CreateField(_fld)

    _fld = ogr.FieldDefn('TAG', ogr.OFTString)
    _fld.SetWidth(25)
    _lyr.CreateField(_fld)

    _perc = progress_percentage(len(rs))

    for _r in rs:
        _perc.next()

        if _r is None:
            continue

        _t, _f = _r

        _ftr = ogr.Feature(_lyr.GetLayerDefn())
        _ftr.SetField('file', _f)
        _ftr.SetField('tag', _get_tag(_f))

        _ftr.SetGeometry(_t.extent().extent().to_polygon().poly)
        _lyr.CreateFeature(_ftr)
        _ftr.Destroy()

    _perc.done()

def main(opts):
    from gio import config
    from gio import file_mag
    import os

    _d_inp = config.get('conf', 'input')
    _f_mak = file_mag.get(os.path.join(_d_inp, 'tasks.txt'))

    from gio import global_task
    if not _f_mak.exists():
        raise Exception('failed to find the tile file')

    _ts = global_task.load(_f_mak)

    from gio import multi_task
    _rs = multi_task.run(_task, [(_r, opts) for _r in multi_task.load(_ts, opts)], opts)
    generate_shp(_rs, opts.output)

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-c', '--cache', dest='cache', default='/mnt/data1/mfeng/test/test1/cache')
    _p.add_argument('-e', '--ext', dest='ext', required=True)
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

