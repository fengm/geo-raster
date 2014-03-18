#!/usr/bin/env python
# -*- coding: utf-8 -*-

def format_command(cmd):
	import re
	_vs = re.split('\s+', cmd.strip())

	if _vs[0] == 'python':
		_vs = _vs[1:]

	if '--logging' in _vs:
		raise Exception('the --logging parameter will be took over by the parallel script')

	return _vs

def format_path(p):
	if p.startswith('/a/'):
		return '/'.join([''] + p.split('/')[3:])

	return p

def usage():
	import argparse

	_p = argparse.ArgumentParser()

	_p.add_argument('-c', '--command', dest='command', required=True)
	_p.add_argument('-r', '--nodes', dest='nodes', required=True, type=int, nargs=2)
	_p.add_argument('-e', '--excludes', dest='excludes', type=int, nargs='*')
	_p.add_argument('-p', '--print', dest='print_cmd', default=False, action='store_true')
	_p.add_argument('--task-num', dest='task_num', type=int, nargs=2, default=[6, 15], help='number of task on lower and higer nodes')

	return _p.parse_args()

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

def main():
	_opts = usage()

	_hosts = range(_opts.nodes[0], _opts.nodes[1] + 1)
	for _e in _opts.excludes if _opts.excludes else []:
		del _hosts[_hosts.index(_e)]

	import subprocess
	import os, sys

	_d_envi = os.getcwd()

	_d_base = format_path(sys.path[0])
	_f_prg = format_command(_opts.command)

	for i in xrange(len(_hosts)):
		_host = 'glcfpro%02d' % _hosts[i]
		print '>>', _host

		_task_num = _opts.task_num[0] if _hosts[i] <= 10 else _opts.task_num[1]

		_d_log = os.path.join(_d_base, 'log', 'pro')
		_log_std = os.path.join(_d_log, 'note_%02d.log' % _hosts[i])

		os.path.exists(_d_log) or os.makedirs(_d_log)
		os.path.exists(_log_std) and os.remove(_log_std)

		_cmd = 'ssh %s "cd %s;python %s --logging %s -ts %d -in %d -ip %d" > %s &' % (_host, _d_envi, ' '.join(_f_prg), log_file(_f_prg[0], _hosts[i]), _task_num, len(_hosts), i, _log_std)

		if _opts.print_cmd:
			print _cmd
		else:
			subprocess.Popen(_cmd, shell=True)

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

