#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: find_empty_dir.py
Author: Min Feng
Version: 0.1
Create: 2013-12-09 11:17:05
Description: identify and remove empty folders under the given path
'''

def list_dir(d):
	import os
	return os.listdir(d)

def check_dir(d_in, d_ot, rm):
	import os

	_ds = []
	for _l in [os.path.join(d_in, _f) for _f in os.listdir(d_in)]:
		if os.path.isdir(_l) and len(os.listdir(_l)) == 0:
			_ds.append(_l)

	print 'found %s empty folders' % len(_ds)
	for _d in _ds:
		print '>', _d

	if d_ot:
		print 'write to', d_ot
		with open(d_ot, 'w') as _fo:
			_fo.write('\n'.join(_ds))

	if rm and raw_input('Are you sure to remove the empty folders?: ').lower() in ['yes', 'y']:
		import shutil
		for _d in _ds:
			print ' - remove', _d
			shutil.rmtree(_d)

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output')
	_p.add_argument('-r', '--remove', dest='remove', action='store_true')

	return _p.parse_args()

def main():
	_opts = usage()
	check_dir(_opts.input, _opts.output, _opts.remove)

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

