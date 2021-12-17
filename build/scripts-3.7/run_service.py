#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: run_service.py
Author: Min Feng
Version: 0.1
Create: 2017-06-07 11:40:03
Description:
'''

def kill_p(k):
    from gio import run_commands
    import re

    _cmd = 'ps -ef'
    _rs = run_commands.run(_cmd)

    for _l in _rs[1].splitlines():
        if 'run_service' in _l:
            continue

        if k not in _l:
            continue

        _vs = re.split('\s+', _l)

        _cmd = 'kill -9 %s' % _vs[1]
        run_commands.run(_cmd, raise_exception=False, check=False)

def main(opts):
    from gio import run_commands
    import time
    import datetime

    _nu = -1.0
    while True:
        _nu += 1

        print('run command #%d' % _nu, datetime.datetime.now())
        try:
            run_commands.run(opts.command, shell=True)
        except KeyboardInterrupt:
            print('\n\n* User stopped the program')
        except Exception:
            print('failed with the command')

        if opts.kill:
            print('clean command')
            kill_p(opts.command)

        print('waiting for restart %ss' % opts.time)
        time.sleep(opts.time)

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-c', '--command', dest='command', required=True)
    _p.add_argument('-t', '--time', dest='time', type=float, default=1.0)
    _p.add_argument('-k', '--kill', dest='kill', type='bool', default=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

