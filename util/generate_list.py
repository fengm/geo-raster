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

	_fs = []
	for _dd in opts.input:
		for _root, _dirs, _files in os.walk(os.path.abspath(_dd)):
			for _file in _files:
				if not opts.pattern or re.search(opts.pattern, _file):
					_fs.append(os.path.join(format_path(_root), _file))

	if opts.output:
		print 'found', len(_fs), 'files'
		with open(opts.output, 'w') as _fo:
			_fo.write('\n'.join(_fs))
	else:
		for _l in _fs:
			print _l

def usage():
	_p = environ_mag.usage(False)

	_p.add_argument('-i', '--input', dest='input', required=True, action='append')
	_p.add_argument('-o', '--output', dest='output')
	_p.add_argument('-p', '--pattern', dest='pattern')

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

