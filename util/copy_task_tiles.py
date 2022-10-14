#!/usr/bin/env python
"""
File: copy_task_tiles.py
Author: Min Feng
Version:  0.1
Create: 2022-07-15 00:56:11
Description: copy task of tiles to another location
"""

import logging

def task(tile, opts, ps, d_out):
    print(tile.tag)

def main(opts):
    from gio import config
    from gio import file_mag
    import os

    import os
    import logging
    from gio import config
    from gio import file_mag
    from gio import global_task
    
    _d_inp = config.get('conf', 'input')
    _f_ref = config.get('conf', 'region')
    _d_out = config.get('conf', 'output')
    
    if global_task.copy(_d_inp, _d_out, _f_ref):
        return

    _rs = global_task.loads(os.path.join(_d_out, 'tasks.txt'))
    _ts = _rs['tiles']

    print('copied %s tasks' % len(_ts))

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-r', '--region', dest='region')
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())]) 