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

def main():
	_opts = _init_env()

	import os
	import re

	_fs = []
	for _dd in _opts.input:
		for _root, _dirs, _files in os.walk(os.path.abspath(_dd)):
			for _file in _files:
				if not _opts.pattern or re.search(_opts.pattern, _file):
					_fs.append(os.path.join(format_path(_root), _file))

	if _opts.output:
		print 'found', len(_fs), 'files'
		with open(_opts.output, 'w') as _fo:
			_fo.write('\n'.join(_fs))
	else:
		for _l in _fs:
			print _l

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

	_p.add_argument('-i', '--input', dest='input', required=True, action='append')
	_p.add_argument('-o', '--output', dest='output')
	_p.add_argument('-p', '--pattern', dest='pattern')

	return _p.parse_args()

def _init_env():
	import os, sys

	_dirs = ['lib', 'libs']
	_d_ins = [os.path.join(sys.path[0], _d) for _d in _dirs if \
			os.path.exists(os.path.join(sys.path[0], _d))]
	sys.path = [sys.path[0]] + _d_ins + sys.path[1:]

	_opts = _usage()

	from gio import logging_util
	logging_util.init(_opts.logging)

	from gio import config
	config.load(_opts.config)

	from gio import file_unzip as fz
	fz.clean(fz.default_dir(_opts.temp))

	return _opts

if __name__ == '__main__':
	main()

