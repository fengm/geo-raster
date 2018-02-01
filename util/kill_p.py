'''
File: kill_p.py
Author: Min Feng
Version: 0.1
Create: 2018-01-12 16:13:23
Description:
'''

def main(opts):
    _cmd = 'ps -ef | grep "%s" | grep -v grep | awk \'{print $2}\' | xargs kill -9' % opts.key

    from gio import run_commands
    run_commands.run(_cmd)

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-k', '--key', dest='key', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

