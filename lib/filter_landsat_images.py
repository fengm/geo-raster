#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: filter_landsat_images.py
Author: Min Feng
Version: 0.1
Create: 2015-03-13 16:16:32
Description: select the Landsat files for the given tiles
'''

def main():
	_opts = _init_env()

	import landsat
	import re

	_ls = []

	# _ts = [_l.strip() for _l in open(_opts.tiles).read().splitlines() if _l.strip()]
	_ts = _opts.tiles
	_ls = []

	with open(_opts.input) as _fi:
		for _l in _fi.read().splitlines():
			_m = re.search('p\d{3}r\d{3}', _l)

			if _m:
				if _m.group() in _ts:
					_ls.append(_l)
				continue

			_m = landsat.parse(_l)
			if _m:
				if _m.tile in _ts:
					_ls.append(_l)
				continue

			raise Exception('failed to parse %s' % _l)

	for _l in _ls:
		print _l

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

	_p.add_argument('input')
	_p.add_argument('tiles', nargs='+')

	return _p.parse_args()

def _init_env():
	import os, sys

	_dirs = ['lib', 'libs']
	_d_ins = [os.path.join(sys.path[0], _d) for _d in _dirs if \
			os.path.exists(os.path.join(sys.path[0], _d))]
	sys.path = [sys.path[0]] + _d_ins + sys.path[1:]

	_opts = _usage()

	import logging_util
	logging_util.init(_opts.logging)

	import config
	config.load(_opts.config)

	import file_unzip as fz
	fz.clean(fz.default_dir(_opts.temp))

	return _opts

if __name__ == '__main__':
	main()

