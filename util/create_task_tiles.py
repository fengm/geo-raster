def main(opts):
    from gio import config
    from gio import file_mag
    import os

    _d_out = config.get('conf', 'output')

    _f_mak = file_mag.get(os.path.join(_d_out, 'tasks.txt'))
    _f_shp = file_mag.get(os.path.join(_d_out, 'tasks.shp'))

    from gio import global_task
    if _f_mak.exists() and not config.getboolean('conf', 'over_write'):
        print('the task tiles is existed')
        return
    
    _f_inp = config.get('conf', 'region')

    _proj = None
    _cell = config.getfloat('conf', 'cell_size')
    
    if opts.geog == True:
        from gio import geo_base as gb
        _proj = gb.proj_from_epsg()
        _cell = _cell / 120000.0
        
        print('use geog projection (%s)' % _cell)

    _ts = global_task.make(_f_inp, image_size=config.getint('conf', 'image_size'), \
                cell_size=_cell, \
                edge=config.getint('conf', 'edge_cell', 1), \
                f_shp=_f_shp, proj=_proj)

    _ps = {}
    for _n, _v in config.cfg.items('conf'):
        _ps[_n] = _v
        
    global_task.save(_ts, _f_mak, _ps)

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-r', '--region', dest='region', required=True)
    _p.add_argument('-i', '--image-size', dest='image_size', type=int, required=True)
    _p.add_argument('--geog', dest='geog', type='bool', default=True)
    _p.add_argument('--cell-size', dest='cell_size', type=float, default=30.0)
    _p.add_argument('--edge-cell', dest='edge_cell', type=int, default=1)
    _p.add_argument('--over-write', dest='over_write', type='bool')
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])
