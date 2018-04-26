#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
File: task_cmd.py
Author: Min Feng
Version: 0.1
Create: 2018-04-26 12:51:21
Description: run task on multiple servers
'''

def format_command(cmd):
    import re
    _vs = re.split('\s+', cmd.strip())

    if '--logging' in _vs:
        raise Exception('the --logging parameter will be took over by the parallel script')

    return _vs

def format_path(p):
    if p.startswith('/a/'):
        return '/'.join([''] + p.split('/')[3:])

    return p

def log_file(p, node):
    import os
    _p, _f = os.path.split(os.path.normpath(p))

    _d = os.path.join(_p, 'log')
    _f = '%s_%02d.log' % (os.path.splitext(_f)[0], node)

    _fp = os.path.join(_d, _f)
    if os.path.exists(_fp):
        _ff, _ee = os.path.splitext(_f)

        _fb = _fp
        for i in xrange(1, 1000000):
            _fb = os.path.join(_d, '%s_%03d%s' % (_ff, i, _ee))
            if os.path.exists(_fb) == False:
                break

        if _fb != _fp:
            os.rename(_fp, _fb)

    return _fp

def main(opts):
    _hosts = opts.nodes
    for _e in opts.excludes if opts.excludes else []:
        if _e in _hosts:
            del _hosts[_hosts.index(_e)]

    from gio import logging_util
    import os

    _d_envi = format_path(os.getcwd())

    _f_log = logging_util.log_file
    _f_prg = format_command(opts.command)

    for i in xrange(len(_hosts)):
        _host = _hosts[i]
        print '>> %s (%s/%s)' % (_host, i, len(_hosts))

        _task_num = opts.task_num

        _log_std = (_f_log[:-4] + '_%s_%02d.log' % (opts.tag, i))
        _log_err = (_f_log[:-4] + '_%s_%02d_err.log' % (opts.tag, i))

        _cmd = 'ssh -o "StrictHostKeyChecking no" -i %s %s "source ~/.bashrc_mine; cd %s; %s -ts %d -in %d -ip %d %s %s %s" >> %s 2>> %s &' % \
                (opts.key, _host, _d_envi, ' '.join(_f_prg), _task_num, len(_hosts), \
                i, '-se' if opts.skip_error else '', '-to %s' % opts.task_order, \
                ('-tw %s' % opts.time_wait) if opts.time_wait > 0 else '', \
                _log_std, _log_err)

        if opts.print_cmd:
            print _cmd
            continue

        os.path.exists(_log_std) and os.remove(_log_std)
        os.path.exists(_log_err) and os.remove(_log_err)

        try:
            _d_log = os.path.dirname(_log_std)
            os.path.exists(_d_log) or os.makedirs(_d_log)
        except Exception:
            pass

        try:
            os.path.exists(_log_std) and os.remove(_log_std)
        except Exception:
            pass

        import subprocess
        subprocess.Popen(_cmd, shell=True)

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-c', '--command', dest='command', required=True)
    _p.add_argument('-k', '--key', dest='key', required=True)
    _p.add_argument('-r', '--nodes', dest='nodes', required=True, nargs='*', type=str)
    _p.add_argument('-e', '--excludes', dest='excludes', nargs='*')
    _p.add_argument('-t', '--tag', dest='tag', required=True)
    _p.add_argument('--print', dest='print_cmd', action='store_true')
    _p.add_argument('-ts', '--task-num', dest='task_num', type=int)
    _p.add_argument('-se', '--skip-error', dest='skip_error', action='store_true')
    _p.add_argument('-tw', '--time-wait', dest='time_wait', type=int, default=0)
    _p.add_argument('-to', '--task-order', dest='task_order', type=int, default=0)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

