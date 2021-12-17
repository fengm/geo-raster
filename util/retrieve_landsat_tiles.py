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
		import gio.landsat
		_cs = gio.landsat.parse(l)
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

	_tt = list(_ts.keys())
	_tt.sort()

	print('found', _nu, 'lines')
	print('exported', len(_tt), 'tiles')
	if not duplicate:
		print(' * combine duplicated records')

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
	print('column:', col)
	print('output:', f_out)
	
	from gio import file_mag
	from gio import file_unzip
	import os
	
	with file_unzip.file_unzip() as _zip:
		_d_out = _zip.generate_file()
		os.makedirs(_d_out)
		
		_f_out = os.path.join(_d_out, os.path.basename(f_out))
		output_tiles(file_mag.get(f_in).get(), _f_out, col, not exclude)
		
		_d_ttt = os.path.dirname(f_out)
		if not _d_ttt:
			_d_ttt = os.path.dirname(os.path.abspath(f_out))
			
		file_unzip.compress_folder(_d_out, _d_ttt, [])

def main(opts):
	if opts.output == None:
		opts.output = (opts.input if opts.input.endswith('.csv') else opts.input[:-4]) + '.csv'

	retrieve_landsat_tiles(opts.input, opts.output, opts.column, \
			opts.exclude_duplicate)

def usage():
	_p = environ_mag.usage(False)

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output')
	_p.add_argument('-c', '--column', dest='column', default='file')
	_p.add_argument('-e', '--exclude-duplicate', dest='exclude_duplicate'\
			, default=False, action='store_true')

	return _p

if __name__ == '__main__':
	from gio import environ_mag
	environ_mag.init_path()
	environ_mag.run(main, [environ_mag.config(usage())])

