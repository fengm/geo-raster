#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-c', '--command', dest='command', required=True)
	_p.add_argument('-r', '--range', dest='range', type=int, default=[1, 20], nargs=2)
	_p.add_argument('-e', '--exclude', dest='exclude', default=[], type=int, nargs='*')

	return _p.parse_args()

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
				if self.cmd in _l and 'ssh ' not in _l and 'sh_kill.py' not in _l:
					_vs = re.split('\s+', _l)
					_ts.append(_vs[1])

			if len(_ts) == 0:
				self.p(' %s no process found' % (self.host))
				return
			else:
				self.p(' %s found %s' % (self.host, len(_ts)))

			_cmd = 'ssh %s kill -9 %s &' % (self.host, ' '.join(_ts))
			try:
				import run_commands
				run_commands.run(_cmd)
			except:
				pass
		finally:
			pass
			# self.p('- ' + self.host)

def main():
	_opts = usage()

	# run the composition 1 step using the servers
	_hosts = range(_opts.range[0], _opts.range[1] + 1)

	for _e in _opts.exclude:
		del _hosts[_hosts.index(_e)]

	_lock = threading.Lock()

	_ps = []
	for i in xrange(len(_hosts)):
		_host = 'glcfpro%02d' % _hosts[i]
		_ps.append(process(_host, _opts.command, _lock))

	for _p in _ps:
		_p.start()

def init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	import logging_util
	logging_util.init()

if __name__ == '__main__':
	init_env()
	main()

