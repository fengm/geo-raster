#!/usr/bin/env python
'''
File: split_raster_tiles.py
Author: Min Feng
Version: 0.1
Create: 2018-07-22 17:33:46
Description:
'''

import logging

def _load(fs, bnd, opts):
    from gio import geo_raster_ex as gx
    from gio import config
    
    _inp = bnd
    _cel = config.getfloat('conf', 'data_cell_size', 0)
    
    if _cel > 0:
        _inp = _inp.scale(cell_size=_cel)
    
    for _f in fs:
        _bnd = gx.read_block(_f, _inp)
        if _bnd:
            # _bnd.data[_bnd.data == 0] = 255
            
            if opts.nodata is not None:
                _bnd.nodata = opts.nodata
                
            if opts.min_value is not None:
                _bnd.data[_bnd.data < opts.min_value] = _bnd.nodata
                
            if opts.max_value is not None:
                _bnd.data[_bnd.data > opts.max_value] = _bnd.nodata
                
            if _cel > 0:
                from gio import agg_band
                
                _agg = config.get('conf', 'data_agg', 'median')
                if _agg == 'median':
                    _out = agg_band.median(_bnd, bnd)
                elif _agg == 'mean':
                    _out = agg_band.mean(_bnd, bnd)
                else:
                    raise Exception('unsupported aggregation method %s' % _agg)
                
                if not _out:
                    return None
                    
                _out.color_table = _bnd.color_table
                _bnd = _out
                
            if not opts.keep_empty:
                if (_bnd.data != _bnd.nodata).sum() == 0:
                    return None
                
            return _bnd
            
    return None
    
def _mask_band(bnd):
    from gio import config
    
    _f_msk = config.get('conf', 'mask')
    if not _f_msk:
        return bnd
        
    logging.debug('mask out %s' % _f_msk)
    
    from gio import geo_base as gb
    from gio import geo_raster as ge
    from gio import file_mag
    
    _gs = [_g for _g, _ in gb.load_shp(file_mag.get(_f_msk).get(), \
            bnd.extent().to_polygon().segment_ratio(10))]
    if len(_gs) <= 0:
        return bnd
        
    logging.info('mask out by %s polygons' % len(_gs))
    from gio import rasterize_band as rb
    rb.mask(bnd, _gs, touched=True)
    return bnd

def _to_coordinate(v, decimals=0, len=3, sign_p='E', sign_n='W'):
    _n = len if decimals == 0 else (len + 1 + decimals)
    _v = ('%%0%d.%df' % (_n, decimals)) % abs(v)
    return _v + (sign_p if v >= 0 else sign_n)

def _to_geo_tile(tile, decimals=0):
    from gio import geo_base as gb
    
    _ex = tile.extent().extent()
    _pt = gb.geo_point(_ex.minx, _ex.maxy, _ex.proj).project_to(gb.proj_from_epsg())
    
    _lat = _to_coordinate(_pt.y, decimals, 2, 'N', 'S')
    _lon = _to_coordinate(_pt.x, decimals, 3, 'E', 'W')
    
    return _lon, _lat

def _task(tile, t, f_inp, d_out, opts):
    import os
    from gio import file_unzip
    from gio import file_mag
    from gio import config
    from gio import geo_raster_ex as gx
    import logging

    _tag = tile.tag
    
    _f_out = tile.file(d_out, '%s.tif' % (t))
    _f_met = tile.file(d_out, '%s.met' % (t))
    
    if file_mag.get(_f_met).exists():
        logging.debug('skip existing result for %s' % _tag)
        return

    with file_unzip.zip() as _zip:
        from gio import metadata
        
        # try:
        _met = metadata.metadata()
        _met.tile = _tag
        
        _bnd = _load(f_inp, tile.extent(), opts)
        if _bnd is None:
            logging.info('skip tile %s' % _tag)
            return
        
        _mask_band(_bnd)

        _f_clr = config.get('conf', 'color_table')
        if _f_clr:
            from gio import geo_raster as ge
            _clr = ge.load_colortable(_f_clr)
            _bnd.color_table = _clr

        _zip.save(_bnd, _f_out)
            
        # finally:
        _met.save(_f_met)

def main(opts):
    import os
    from gio import file_mag
    from gio import config

    _d_out = opts.output
    if not _d_out:
        return

    _f_mak = file_mag.get(os.path.join(_d_out, 'tasks.txt'))
    _f_shp = file_mag.get(os.path.join(_d_out, 'tasks.shp'))

    from gio import global_task
    if not _f_mak.exists():
        if not opts.input:
            raise Exception('need to previde input extent file')

        _f_inp = file_mag.get(opts.region)
        if not _f_inp:
            raise Exception('need to provide extent file for initailization')

        _image_size = config.getint('conf', 'image_size', 3000)
        _cell_size = config.getfloat('conf', 'cell_size', 30)

        _tag = config.get('conf', 'tag')
        if _tag is None:
            raise Exception('need to provide tag')

        _proj = config.get('conf', 'proj')
        _edge = config.getint('conf', 'edge')

        from gio import geo_base as gb
        if _proj:
            _proj = gb.proj_from_proj4(_proj)

        if _proj.IsGeographic() and opts.geog == True:
            _proj = gb.proj_from_epsg()
            _cell_size = _cell_size / 120000.0
            
            print('use geog projection (%s)' % _cell_size)

        print(('projection: %s' % _proj))
        print(('tag: %s, image size: %s, cell size: %s, edge: %s' % (_tag, _image_size, _cell_size, _edge)))

        _ts = global_task.make(_f_inp.get(), None, f_shp=_f_shp, \
                edge=_edge, \
                proj=_proj, \
                image_size=_image_size, \
                cell_size=_cell_size)

        global_task.save(_ts, _f_mak, \
                {'edge': _edge, \
                    't': _tag, 'proj': _proj.ExportToProj4()})
                    
        return
    
    _gs = global_task.loads(_f_mak)
    _ms = _gs['params']
    _ts = _gs['tiles']

    _tt = opts.test_tile
    if _tt:
        _ts = [_t for _t in _ts if _t.tag in _tt]

    _tt = _ms.get('t', opts.tag) if opts.tag is None else opts.tag
    _d_out = opts.output

    from gio import multi_task
    multi_task.run(_task, [(_r, _tt, opts.input, os.path.join(_d_out, 'data'), opts) \
            for _r in multi_task.load(_ts, opts)], opts)
            
    if not opts.build_index:
        return
    
    print('build index file ({}.tif)'.format(opts.tag))
    _f_idx = os.path.join(_d_out, 'list', '%s.shp' % opts.tag)
    
    from gio import run_commands
    _cmd = 'generate_tiles_extent.py -i {} -e {}.tif -o {} --over-write true'.format(\
                       _d_out, opts.tag, _f_idx)
    
    run_commands.run(_cmd)
    print('index file: %s' % _f_idx)

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', nargs='+')
    _p.add_argument('-r', '--region', dest='region')
    _p.add_argument('-t', '--tag', dest='tag')
    
    _p.add_argument('--geog', dest='geog', type='bool', default=True)
    _p.add_argument('-p', '--proj', dest='proj', default='EPSG:4326')
    
    _p.add_argument('-s', '--image-size', dest='image_size', default=3000, type=int)
    _p.add_argument('-c', '--cell-size', dest='cell_size', default=30.0, type=float)
    _p.add_argument('-e', '--edge', dest='edge', type=int, default=0)
    _p.add_argument('-m', '--mask', dest='mask')
    
    _p.add_argument('--nodata', dest='nodata', type=float)
    _p.add_argument('--min-value', dest='min_value', type=float)
    _p.add_argument('--max-value', dest='max_value', type=float)
    _p.add_argument('--keep-empty', dest='keep_empty', type='bool')
    _p.add_argument('-b', '--build-index', dest='build_index', type='bool')
    
    _p.add_argument('--data-cell-size', dest='data_cell_size', type=float)
    _p.add_argument('--data-agg', dest='data_agg', default='median')
    
    _p.add_argument('--geo-tile', dest='geo_tile', type='bool')
    _p.add_argument('--geo-tile-decimals', dest='geo_tile_decimals', type=int, default=0)
    _p.add_argument('--color-table', dest='color_table')
    _p.add_argument('-o', '--output', dest='output', required=True)
    _p.add_argument('--test-tile', dest='test_tile')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])
