#!/usr/bin/env python
# encoding: utf-8

import logging

def retrieve_tile(l):
	import re

	_file = l.replace(',', '_')

	_m = re.search('p\d{3}r\d{3}', l)
	if _m:
		return _m.group(), _file
	else:
		import landsat
		_cs = landsat.parse(l)
		if _cs == None:
			return None, _file

		return _cs.tile, _file

def output_tiles(f_in, f_out, col, duplicate):
	_ts = {}
	_nu = 0
	for _l in open(f_in).read().splitlines():
		_nu += 1

		_tile, _file = retrieve_tile(_l)
		if _tile == None:
			continue

		if (_tile not in _ts):
			_ts[_tile] = [_tile, 1, [_file]]
		else:
			_ts[_tile][1] += 1
			_ts[_tile][2].append(_file)

	_tt = _ts.keys()
	_tt.sort()

	print 'found', _nu, 'lines'
	print 'exported', len(_tt), 'tiles'
	if not duplicate:
		print ' * combine duplicated records'

	_cols = ['tile', 'num', col]
	_ls = [','.join(_cols)]

	for _t in _tt:
		if duplicate:
			for _f in _ts[_t][2]:
				_ls.append(','.join([_ts[_t][0], str(_ts[_t][1]), _f]))
		else:
			_ls.append(','.join([_ts[_t][0], str(_ts[_t][1]), ';'.join(_ts[_t][2])]))

	with open(f_out, 'w') as _fo:
		_fo.write('\n'.join(_ls))

def retrieve_landsat_tiles(f_in, f_out, col, exclude):
	print 'column:', col
	print 'output:', f_out

	output_tiles(f_in, f_out, col, not exclude)

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output')
	_p.add_argument('-c', '--column', dest='column', default='file')
	_p.add_argument('-e', '--exclude-duplicate', dest='exclude_duplicate'\
			, default=False, action='store_true')

	_opts = _p.parse_args()
	if _opts.output == None:
		_opts.output = (_opts.input if _opts.input.endswith('.csv') else _opts.input[:-4]) + '.csv'

	return _opts

def main():
	_opts = init_env()

	retrieve_landsat_tiles(_opts.input, _opts.output, _opts.column, \
			_opts.exclude_duplicate)

def init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	_opts = usage()

	import logging_util
	logging_util.init(_opts.logging)

	return _opts

if __name__ == '__main__':
	main()

