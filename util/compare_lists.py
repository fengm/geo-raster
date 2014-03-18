#!/usr/bin/env python
# encoding: utf-8

'''
File: compare_lists.py
Author: Min Feng
Version: 0.1
Create: 2013-04-15 12:01:10
Description: compare two lists and output the union and differences
'''

def load_file(f, reg):
	import re

	_ls = []
	for _l in open(f).read().splitlines():
		_m = re.search(reg, _l)
		if not _m:
			continue

		_ls.append(_m.group())
	return _ls

def remove_duplication(ls):
	_ls = []
	for _l in ls:
		if _l not in _ls:
			_ls.append(_l)
	return _ls

def compare_files(f1, f2, fo, reg):
	_ts1 = load_file(f1, reg)
	_ts2 = load_file(f2, reg)

	_ssc = remove_duplication([_t for _t in _ts1 if _t in _ts2])
	_ssa = remove_duplication(_ts1 + _ts2)
	_ss1 = remove_duplication([_t for _t in _ts1 if _t not in _ts2])
	_ss2 = remove_duplication([_t for _t in _ts2 if _t not in _ts1])

	print 'common:', len(_ssc)
	print 'all in:', len(_ssa)
	print '1 > 2 :', len(_ss1)
	print '2 > 1 :', len(_ss2)

	with open(fo[:-4] + '_c' + fo[-4:], 'w') as _f:
		_f.write('\n'.join(_ssc))

	with open(fo[:-4] + '_a' + fo[-4:], 'w') as _f:
		_f.write('\n'.join(_ssa))

	with open(fo[:-4] + '_1' + fo[-4:], 'w') as _f:
		_f.write('\n'.join(_ss1))

	with open(fo[:-4] + '_2' + fo[-4:], 'w') as _f:
		_f.write('\n'.join(_ss2))

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-i', '--input', dest='input', required=True, nargs=2)
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('-r', '--reg', dest='reg', default='p\d{3}r\d{3}')

	return _p.parse_args()

if __name__ == '__main__':
	_opts = usage()
	compare_files(_opts.input[0], _opts.input[1], _opts.output, _opts.reg)

