#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading

class process(threading.Thread):

    def __init__(self, host, cmd, lock):
        threading.Thread.__init__(self)

        self.host = host
        self.cmd = cmd
        self.lock = lock

    def p(self, txt):
        with self.lock:
            print txt

    def run(self):
        # self.p('+ ' + self.host)

        import subprocess
        import re

        try:
            _cmd = 'ssh %s ps -ef' % (self.host)
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
            # self.p('- ' + self.host)

def main(opts):
    # run the composition 1 step using the servers
    _hosts = range(opts.range[0], opts.range[1] + 1)

    for _e in opts.exclude:
        del _hosts[_hosts.index(_e)]

    _lock = threading.Lock()

    _ps = []
    for i in xrange(len(_hosts)):
        _host = 'glcfpro%02d' % _hosts[i]
        if _host == 'glcfpro02':
            _host = 'glcfing10'
        _ps.append(process(_host, opts.command, _lock))

    for _p in _ps:
        _p.start()

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-c', '--command', dest='command', required=True)
    _p.add_argument('-r', '--range', dest='range', type=int, default=[1, 20], nargs=2)
    _p.add_argument('-e', '--exclude', dest='exclude', default=[], type=int, nargs='*')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

