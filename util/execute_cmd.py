'''
File: execute_cmd.py
Author: Min Feng
Version: 0.1
Create: 2017-05-05 23:17:08
Description:
'''

def main(opts):
	from gio import run_commands
	import datetime
	import time

	_d = datetime.datetime.now()
	_n = 0
	while(True):
		_c = datetime.datetime.now()
		if _n > 0 and (_c - _d).hour < 24:
			time.sleep(60 * 10)
			continue

		_d = _c

		_n += 1
		print 'run command', _n, _d

		_rs = run_commands.run(opts.command)
		print _rs[1]

def usage():
	_p = environ_mag.usage(False)

	_p.add_argument('-c', '--command', dest='command', required=True)
	_p.add_argument('--hour', dest='hour', required=True, type=int)

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

