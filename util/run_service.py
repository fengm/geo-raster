'''
File: run_service.py
Author: Min Feng
Version: 0.1
Create: 2017-06-07 11:40:03
Description:
'''

def main(opts):
	from gio import run_commands
	import time
	import datetime

	_nu = -1.0
	while True:
		_nu += 1

		print 'run command #%d' % _nu, datetime.datetime.now()
		try:
			run_commands.run(opts.command, shell=True)
		except Exception:
			print 'failed with the command'

		time.sleep(opts.time)

def usage():
	_p = environ_mag.usage(False)

	_p.add_argument('-c', '--command', dest='command', required=True)
	_p.add_argument('-t', '--time', dest='time', type=float, default=3.0)

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

