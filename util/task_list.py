#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
File: task_list.py
Author: Min Feng
Version: 0.1
Create: 2018-04-26 12:58:02
Description:
'''

import threading

class process(threading.Thread):

    def __init__(self, host, cmd, opts, lock):
        threading.Thread.__init__(self)

        self.host = host
        self.cmd = cmd
        self.opts = opts
        self.lock = lock

    def p(self, txt):
        with self.lock:
            print txt

    def run(self):
        import subprocess
        import re

        try:
            _cmd = 'ssh -o "StrictHostKeyChecking no" -i %s %s ps -ef' % (self.opts.key, self.host)
            _p = subprocess.Popen(_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            _o = _p.communicate()
            if not (_o and _o[0]):
                return

            _ts = []
            for _l in _o[0].splitlines()[1:]:
                if self.cmd in _l and 'ssh ' not in _l and 'sh_list.py ' not in _l:
                    _vs = re.split('\s+', _l)
                    _ts.append(_vs[1])

            self.p(self.host + ': ' + ' '.join([str(len(_ts)), '<%s>' % ','.join(_ts)]))

        finally:
            pass

def main(opts):
    _hosts = opts.nodes
    for _e in opts.excludes if opts.excludes else []:
        if _e in _hosts:
            del _hosts[_hosts.index(_e)]

    _lock = threading.Lock()

    _ps = []
    for i in xrange(len(_hosts)):
        _host = _hosts[i]
        _ps.append(process(_host, opts.command, opts, _lock))

    for _p in _ps:
        _p.start()

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-c', '--command', dest='command', required=True)
    _p.add_argument('-r', '--nodes', dest='nodes', required=True, nargs='+')
    _p.add_argument('-k', '--key', dest='key', required=True)
    _p.add_argument('-e', '--excludes', dest='excludes', default=[], nargs='*')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

