#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: copy_s3_files.py
Author: Min Feng
Version: 0.1
Create: 2018-02-27 13:25:48
Description: copy files to S3 and skip the existing ones
'''

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

    return d_out + ('' if d_out.endswith('/') else '/') + _p

def upload_file(f, b, d_out):
    from gio import file_mag
    from gio import config
    import logging
    
    _out = update_path(f, b, d_out)
    _key = file_mag.get(_out)
    
    if config.getboolean('conf', 'debug'):
        print(f, _out)

    if not file_mag.get(f).exists():
        logging.warning('missing file %s' % f)
        return
            
    if not _key.exists():
        _key.put(file_mag.get(f).get())
        
    return _out
    
def load_list(f, b, d_out):
    # from gio import file_mag
    _fs = open(f).read().strip().splitlines()
    
    _ls = []
    for _f in _fs:
        _ls.append((_f, b, d_out))

    return _ls

def main(opts):
    from gio import multi_task
    import os

    _ps = []
    _s = 0.0
    for _f, _b, _d_out in multi_task.load(load_list(opts.input, opts.base_path, \
            opts.output), opts):

        if not _f:
            continue
        
        if opts.check_size:
            _s += os.path.getsize(_f) / (1024.0 * 1024.0 * 1024.0)

        _ps.append((_f, _b, _d_out))
        
    for _i in range(min(len(_ps), 3)):
        print('...', _ps[_i])

    if opts.check_size:
        print('size', '%0.3fGb' % _s)

    _rs = multi_task.run(upload_file, _ps, opts)
    del _rs

    print('done')

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-ak', '--access-key', dest='access_key', default=None)
    _p.add_argument('-sk', '--secret-key', dest='secret_key', default=None)

    _p.add_argument('-c', '--check-size', dest='check_size', type='bool', default=False)

    _p.add_argument('-p', '--base-path', dest='base_path')
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])
