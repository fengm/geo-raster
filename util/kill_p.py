#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: kill_p.py
Author: Min Feng
Version: 0.1
Create: 2018-01-12 16:13:23
Description:
'''

def main(opts):
    # _cmd = 'ps -ef | grep "%s" | grep -v grep | awk \'{print $2}\' | xargs kill -9' % opts.key
    from gio import run_commands
    import re

    _cmd = 'ps -ef'
    _rs = run_commands.run(_cmd)
    for _l in _rs[1].splitlines():
        if 'kill_p.py' in _l:
            continue

        if opts.key not in _l:
            continue

        _vs = re.split('\s+', _l)
        print(_l)

        _cmd = 'kill -9 %s' % _vs[1]
        run_commands.run(_cmd, raise_exception=False, check=False)

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-k', '--key', dest='key', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

