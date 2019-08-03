'''
File: split_raster_tiles.py
Author: Min Feng
Version: 0.1
Create: 2018-07-22 17:33:46
Description:
'''

def _task(tile, t, f_inp, d_out, ps):
    import os
    from gio import file_unzip
    from gio import file_mag
    from gio import geo_raster_ex as gx
    import logging

    _tag = tile.tag
    _d_out = os.path.join(d_out, 'h%03d' % tile.col, 'v%03d' % tile.row)

    if len(list(file_mag.get(_d_out).list())) >= 1:
        logging.debug('skip existing result for %s' % _tag)
        return

    _mak = tile.extent()
    with file_unzip.file_unzip() as _zip:
        _bnd = gx.geo_band_stack_zip.from_shapefile(f_inp, file_unzip=_zip)\
            .read_block(_mak)

        _d_tmp = _zip.generate_file()
        os.path.exists(_d_tmp) or os.makedirs(_d_tmp)

        _f_out = os.path.join(_d_tmp, '%s_%s.tif' % (t, _tag))
        _bnd.save(_f_out)

        file_unzip.compress_folder(_d_tmp, _d_out, [])

def main(opts):
    import os
    from gio import file_mag
    from gio import config

    _d_out = opts.output

    _f_mak = file_mag.get(os.path.join(_d_out, 'tasks.txt'))
    _f_shp = file_mag.get(os.path.join(_d_out, 'tasks.shp'))

    from gio import global_task
    if not _f_mak.exists():
        if not opts.input:
            raise Exception('need to previde input extent file')

        _f_inp = file_mag.get(opts.input)
        if not _f_inp:
            raise Exception('need to provide extent file for initailization')

        _image_size = config.getint('conf', 'image_size', 3000)
        _cell_size = config.getfloat('conf', 'cell_size', 30)

        if _image_size is None or _cell_size is None:
            raise Exception('require specified cell size and image size')

        _tag = config.get('conf', 'tag')
        if _tag is None:
            raise Exception('need to provide tag')

        _proj = config.get('conf', 'proj')
        _edge = config.getint('conf', 'edge')

        print('projection: %s' % _proj)
        print('tag: %s, image size: %s, cell size: %s, edge: %s' % (_tag, _image_size, _cell_size, _edge))

        from gio import geo_base as gb
        _ts = global_task.make(_f_inp.get(), None, f_shp=_f_shp, \
                edge=_edge, \
                proj=gb.proj_from_proj4(_proj), \
                image_size=_image_size, \
                cell_size=_cell_size)

        global_task.save(_ts, _f_mak, \
                {'input': opts.input, 'output': opts.output, 'edge': _edge, \
                    't': _tag, 'proj': _proj})
    else:
        _gs = global_task.loads(_f_mak)
        _ms = _gs['params']
        _ts = _gs['tiles']

        opts.input = opts.input if opts.input is not None else _ms['input']
        opts.output = opts.output if opts.output is not None else _ms['output']
        _tt = _ms.get('t', opts.tag) if opts.tag is None else opts.tag

        _d_out = opts.output

        from gio import multi_task
        multi_task.run(_task, [(_r, _tt, opts.input, os.path.join(_d_out, 'data'), opts) \
                for _r in multi_task.load(_ts, opts)], opts)

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input')
    _p.add_argument('-e', '--edge', dest='edge', type=int, default=1)
    _p.add_argument('-t', '--tag', dest='tag')
    _p.add_argument('-p', '--proj', dest='proj', \
        default='+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs')
    _p.add_argument('-s', '--image-size', dest='image_size', default=3000, type=int)
    _p.add_argument('-c', '--cell-size', dest='cell_size', default=30.0, type=float)
    _p.add_argument('-o', '--output', dest='output')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])
