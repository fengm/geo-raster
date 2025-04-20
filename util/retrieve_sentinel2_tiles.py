#!/usr/bin/env python
# encoding: utf-8

import logging
import re
import os

def retrieve_tile(l):
    _file = l.replace(',', '_')

    _m = re.search(r'_T(\d{2}\w{3})_', l) \
            or re.search(r'S2\w_(\d{2}\w{3})_', l) \
            or re.search(r'S2\w_(\d\w{3})_', l)
    
    if not _m:
        return None, _file
    
    _d = _m.group(1)
    if len(_d) < 5:
        _d = '0' + _d
    
    return _d, _file

def output_tiles(f_in, f_out, col, duplicate):
    from gio import file_mag
    
    _ts = {}
    _nu = 0
    _ds = []
    
    _bb = file_mag.get(f_in).read()
    for _l in _bb.decode('utf-8').strip().splitlines():
        _nu += 1

        _tile, _file = retrieve_tile(_l)
        if _tile == None:
            _ds.append(_file)
            continue

        if (_tile not in _ts):
            _ts[_tile] = [_tile, 1, [_file]]
        else:
            _ts[_tile][1] += 1
            _ts[_tile][2].append(_file)

    _tt = list(_ts.keys())
    _tt.sort()

    print('found', _nu, 'lines')
    print('exported', len(_tt), 'tiles')
    if not duplicate:
        print(' * combine duplicated records')

    _cols = ['tile', 'num', col]
    _ls = [','.join(_cols)]

    for _t in _tt:
        if duplicate:
            for _f in _ts[_t][2]:
                _ls.append(','.join([_ts[_t][0], str(_ts[_t][1]), _f]))
        else:
            _ls.append(','.join([_ts[_t][0], str(_ts[_t][1]), ';'.join(_ts[_t][2])]))

    with open(f_out, 'w') as _fo:
        _fo.write('\n'.join(_ls))
    
    if len(_ds):    
        print('failed to parse %s lines' % len(_ds))
        for _i in range(min(10, len(_ds))):
            print(_ds[_i])

def retrieve_landsat_tiles(f_in, f_out, col, exclude):
    print('column:', col)
    print('output:', f_out)
    
    from gio import file_mag
    from gio import file_unzip
    import os
    
    with file_unzip.file_unzip() as _zip:
        _d_out = _zip.generate_file()
        os.makedirs(_d_out)
        
        _f_out = os.path.join(_d_out, os.path.basename(f_out))
        output_tiles(f_in, _f_out, col, not exclude)
        
        _d_ttt = os.path.dirname(f_out)
        if not _d_ttt:
            _d_ttt = os.path.dirname(os.path.abspath(f_out))
            
        file_unzip.compress_folder(_d_out, _d_ttt, [])
        
def default_output_file(f):
    for _e in ['.txt', '.txt.gz', '.csv', '.csv.gz']:
        if f.endswith(_e):
            return f[:-1*len(_e)] + '.csv'
        
    return f

def main(opts):
    if opts.output == None:
        opts.output = default_output_file(opts.input)

    retrieve_landsat_tiles(opts.input, opts.output, opts.column, \
            opts.exclude_duplicate)
    
    if opts.execute:
        print('generate tiling shapefile')
        _cmd = 'tiles_csv2shp.py --tiling mgrs -i %s -ts %s' % (opts.output, opts.task_num)
        from gio import run_commands
        run_commands.run(_cmd)

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-o', '--output', dest='output')
    _p.add_argument('-c', '--column', dest='column', default='file')
    _p.add_argument('-e', '--execute', dest='execute', type='bool')
    _p.add_argument('-d', '--exclude-duplicate', dest='exclude_duplicate', type='bool')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

