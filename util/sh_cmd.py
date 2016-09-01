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
	_hosts = range(opts.nodes[0], opts.nodes[1] + 1)
	for _e in opts.excludes if opts.excludes else []:
		del _hosts[_hosts.index(_e)]

	import os, sys

	_d_envi = format_path(os.getcwd())

	_d_base = format_path(sys.path[0])
	_f_prg = format_command(opts.command)

	# only include nodes for processing
	_n_inc = None if ((opts.include == None) or (len(opts.include) == 0)) else opts.include

	for i in xrange(len(_hosts)):
		_host = 'glcfpro%02d' % _hosts[i]

		if _n_inc != None and (_hosts[i] not in _n_inc):
			print ' - skip', _host
			continue

		print '>>', _host

		_task_num = opts.task_num[0] if _hosts[i] <= 10 else opts.task_num[1]

		_d_log = os.path.join(_d_base, 'log', 'pro')
		_log_std = os.path.join(_d_log, 'note_%02d.log' % _hosts[i])

		_cmd = 'ssh %s "cd %s;python %s --logging %s -ts %d -in %d -ip %d %s %s" > %s &' % \
				(_host, _d_envi, ' '.join(_f_prg), log_file(_f_prg[0], _hosts[i]), _task_num, len(_hosts), \
				i, '-se' if opts.skip_error else '', ('-tw %s' % opts.time_wait) if opts.time_wait > 0 else '', \
				_log_std)

		if opts.print_cmd:
			print _cmd
			continue

		try:
			os.path.exists(_d_log) or os.makedirs(_d_log)
		except Exception:
			pass

		try:
			os.path.exists(_log_std) and os.remove(_log_std)
		except Exception:
			pass

		import subprocess
		subprocess.Popen(_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def usage():
	_p = environ_mag.usage(False)

	_p.add_argument('-c', '--command', dest='command', required=True)
	_p.add_argument('-r', '--nodes', dest='nodes', required=True, type=int, nargs=2)
	_p.add_argument('-e', '--excludes', dest='excludes', type=int, nargs='*')
	_p.add_argument('-i', '--include', dest='include', type=int, nargs='*', \
			help='Only nodes listed in the param will be run. Used for reruning jobs for specified nodes.')
	_p.add_argument('-p', '--print', dest='print_cmd', default=False, action='store_true')
	_p.add_argument('-ts', '--task-num', dest='task_num', type=int, nargs=2, default=[5, 12], \
			help='number of task on lower and higer nodes')
	_p.add_argument('-se', '--skip-error', dest='skip_error', action='store_true')
	_p.add_argument('-tw', '--time-wait', dest='time_wait', type=int, default=0)

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

