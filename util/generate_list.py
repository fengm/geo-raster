#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: generate_list.py
Author: Min Feng
Version: 0.1
Create: 2015-03-10 11:44:38
Description: generate list of files in a folder
'''

def format_path(f):
	import re

	_m = re.match('/a/[^/]+(/.+)', f)
	if _m:
		return _m.group(1)

	return f

def main(opts):
	import os
	import re
	import logging

	_fs = []
	for _dd in opts.input:
		for _root, _dirs, _files in os.walk(os.path.abspath(_dd)):
			for _file in _files:
				if not opts.pattern or re.search(opts.pattern, _file):
					_f = os.path.join(format_path(_root), _file)

					if os.path.getsize(_f) <= 0:
						logging.warning('skip zero size file: %s' % _f)
						continue

					_fs.append(_f)

	if len(_fs) == 0:
		print ' * no file was found'
		return

	if opts.output:
		print 'found', len(_fs), 'files'

		(lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(os.path.abspath(opts.output)))

		with open(opts.output, 'w') as _fo:
			_fo.write('\n'.join(_fs) + '\n')

		if opts.extent:
			print 'generate raster extent'

			_cmd = 'raster_extent2shp.py -i %s ' % opts.output
			_tsk = '-in %s -ip %s -ts %s %s -tw %s -to %s' % ( \
					opts.instance_num, opts.instance_pos, opts.task_num, \
							'-se' if opts.skip_error else '', opts.time_wait, opts.task_order)

			from gio import run_commands
			run_commands.run(_cmd + _tsk)
	else:
		for _l in _fs:
			print _l

def usage():
	_p = environ_mag.usage(True)

	_p.add_argument('-i', '--input', dest='input', nargs='+', required=True)
	_p.add_argument('-z', '--skip-zero-file', dest='skip_zero_file', action='store_true')
	_p.add_argument('-o', '--output', dest='output')
	_p.add_argument('-p', '--pattern', dest='pattern')

	_p.add_argument('-e', '--extent', dest='extent', action='store_true', \
			help='run raster_extent2shp after the list is generated')

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

