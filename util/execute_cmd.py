#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: execute_cmd.py
Author: Min Feng
Version: 0.1
Create: 2017-05-05 23:17:08
Description:
'''

def main(opts):
	from gio import run_commands
	from gio import config
	import datetime
	import time
	import sys

	_d = datetime.datetime.now()
	_n = 0

	while(True):
		_c = datetime.datetime.now()
		if _n > 0 and (_c - _d).total_seconds() < opts.second:
			time.sleep(opts.second / 100)

			print('.', end=' ')
			sys.stdout.flush()
			continue

		if _n > 0:
			print('')

		_d = _c
		_n += 1
		print('run command', _n, _d)

		_rs = run_commands.run(opts.command)
		print(_rs[1])

		_m = config.getint('conf', 'max_run', -1)
		if _m > 0:
			if _n >= _m:
				break

		if opts.second <= 0:
			break

def usage():
	_p = environ_mag.usage(False)

	_p.add_argument('-c', '--command', dest='command', required=True)
	_p.add_argument('-n', '--max-run', dest='max_run', type=int)
	_p.add_argument('-s', '--second', dest='second', required=True, type=int)

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

