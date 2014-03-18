#!/usr/bin/env python
# -*- coding: utf-8 -*-

def convert_type(c):
	c = c.lower()

	if c == 'forest':
		return 1
	if c in ['nonforest', 'water', 'grass', 'cropland', 'others', 'crop', 'urban']:
		return 9
	if c in [None, '', 'unknown']:
		return 0

	if c in ['cloud', 'shadow', 'nodata', 'badimage', 'badimages']:
		return -1

	print 'unrecognized type:', c
	assert(False)

def convert_fcc(fcc):
	if fcc == '':
		return -1, -1

	if len(fcc) == 2:
		return int(fcc[0]), int(fcc[1])

	_fcc = int(fcc)
	if _fcc in [4]:
		return 9, 9

	return -1, -1

def convert_fccs(fcc1990, fcc2000):

	_fc1990, _fc2000 = convert_fcc(fcc1990)
	_fc2000, _fc2005 = convert_fcc(fcc2000)

	_vs = {}
	_vs['f_f1990'] = _fc1990
	_vs['f_f2000'] = _fc2000
	_vs['f_f2005'] = _fc2005

	return _vs

def load_prob(f):
	import csv_util

	print 'load scene prob', f

	_cs = {}
	for _l in csv_util.open(f):
		_s = _l.get('tile')
		_v = _l.getfloat('incl_prob')

		_cs[_s] = _v

	return _cs

def load_tiles(f, ms):
	import os
	if os.path.isdir(f):
		for _f in os.listdir(f):
			load_tiles(os.path.join(f, _f), ms)
		return

	import csv_util
	import re

	print 'loading sample tiles', f
	for _l in csv_util.open(f):
		_x = _l.get('x')
		_y = _l.get('y')

		_id = '%s_%s' % (_x, _y)
		_t = re.search('p\d{3}r\d{3}', f).group()
		ms[_id] = _t

def append_cols(f_in, f_ot, f_po, f_ts):
	import csv_util

	_ps = None if not f_po else load_prob(f_po)
	_ts = None
	if f_ts:
		_ts = {}
		load_tiles(f_ts, _ts)

	_cs = None
	_ys = [1975, 1990, 2000, 2005]
	_ls = []

	for _l in csv_util.open(f_in):
		_ms = {}

		if _ts:
			_id = '%s_%s' % (_l.get('x'), _l.get('y'))
			if _id not in _ts:
				raise Exception('failed to find tile info for loc %s' % _id)

			_tile = _ts[_id]
			_ms['tile'] = _tile
		else:
			_tile = _l.get('tile')

		for _y in _ys:
			_t = 'y%s' % _y
			_ms['f_%s' % _t] = convert_type(_l.get(_t))

		_ms.update(convert_fccs(_l.get('fcc1990'), _l.get('fcc2000')))
		if _cs == None:
			_cs = sorted(_ms.keys())
			_ls.append(_l.info.sep.join(_l.info.cols + _cs))

		if _ps:
			if _tile not in _ps:
				print 'eeee', _tile
				raise Exception('failed to find scene level inclusion prob %s' % _tile)

			_l.set('prob', _l.getfloat('prob') * _ps[_tile] * 10000)

		_ls.append(_l.info.sep.join(_l.vals + ['%s' % _ms[_k] for _k in _cs]))

	with open(f_ot, 'w') as _fo:
		_fo.write('\n'.join(_ls))

def main():
	_opts = _init_env()

	append_cols(_opts.input, _opts.output, _opts.scene_prob, _opts.tiles_path)

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('--scene-prob', dest='scene_prob')
	_p.add_argument('--tiles-path', dest='tiles_path')


	return _p.parse_args()

def _init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	_opts = _usage()

	import logging_util
	logging_util.init(_opts.logging)

	import config
	config.load(_opts.config)

	return _opts

if __name__ == '__main__':
	main()


