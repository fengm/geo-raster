#!/usr/bin/env python
# -*- coding: utf-8 -*-

class forest_metrics:

	def __init__(self, cols):
		import numpy as np

		self.met_num = np.zeros((len(cols) + 1, len(cols) + 1))
		self.met_wet = np.zeros((len(cols) + 1, len(cols) + 1))

		self.columns = cols

	def _cal_sum_metrics(self, met, isnum):
		import numpy as np

		_len = len(self.columns)
		for _row in xrange(_len):
			_sum = met[_row, :_len].sum()
			met[_row, _len] = _sum if isnum else ((met[_row, _row] / _sum) if _sum > 0 else np.nan)
		for _col in xrange(_len):
			_sum = met[:_len, _col].sum()
			met[_len, _col] = _sum if isnum else ((met[_col, _col] / _sum) if _sum > 0 else np.nan)

		_sum = met[:_len, :_len].sum()
		met[_len, _len] = _sum if isnum else (sum([met[_row, _row] for _row in range(_len)]) / _sum)

		if isnum: return
		for _row in xrange(_len):
			for _col in xrange(_len):
				if np.isnan(met[_row, _col]):
					continue
				met[_row, _col] = met[_row, _col] * 100.0 / _sum

	def cal_sum_metrics(self):
		self._cal_sum_metrics(self.met_num, True)
		self._cal_sum_metrics(self.met_wet, False)

	def _format_output_val(self, met, row, col, isint):
		import numpy as np

		if row < met.shape[0] - 1 and col < met.shape[1] - 1:
			if isint:
				return '%d' % met[row, col]
			else:
				return '%.2f' % met[row, col]
		else:
			if np.isnan(met[row, col]):
				return 'nan'
			else:
				if isint:
					return '%d' % met[row, col]
				else:
					return '%.2f%%' % (met[row, col] * 100)

	def _output_metrics(self, met, cols, isfloat, ls):
		_cols = [''] + cols + ['QA']

		ls.append('\t'.join(_cols))
		for _row in xrange(met.shape[0]):
			ls.append('\t'.join([_cols[_row + 1]] + [self._format_output_val(met, _row, _col, isfloat) for _col in xrange(met.shape[1])]))

	def output_metrics(self, ls):
		ls.append('')
		ls.append('num of samples')
		self._output_metrics(self.met_num, self.columns, True, ls)

		ls.append('')
		ls.append('accuracy metrics')
		self._output_metrics(self.met_wet, self.columns, False, ls)

	def output_columns(self, tag):
		import numpy as np
		_format_val = lambda x: '' if np.isnan(x) else '%.2f' % (x * 100)

		_ks = {}
		for _pos in xrange(len(self.columns)):
			_ks['%s_%s_u' % (tag, self.columns[_pos].lower())] = _format_val(self.met_wet[_pos, -1])
			_ks['%s_%s_p' % (tag, self.columns[_pos].lower())] = _format_val(self.met_wet[-1, _pos])
		_ks['%s_all' % tag] = _format_val(self.met_wet[-1, -1])
		return _ks

def cal_forest_agree_metric(f, tile, year, ls, ks):

	_met = forest_metrics(['F', 'N'])
	_convert_pos = lambda(lc): 0 if int(lc) == 1 else 1

	import csv_util
	for _r in csv_util.open(f):

		_v_ref = _r.get('f_y%s' % year)
		_v_val = _r.get('f_f%s' % year)

		_b_val = _r.getint('f_valid')
		_v_wet = _r.getfloat('prob')
		_v_til = _r.get('tile')

		if _b_val == 0:
			continue

		if tile and _v_til != tile:
			continue

		_met.met_num[_convert_pos(_v_val), _convert_pos(_v_ref)] += 1
		_met.met_wet[_convert_pos(_v_val), _convert_pos(_v_ref)] += 1 / _v_wet

	_met.cal_sum_metrics()

	ls.append('')
	ls.append('> year %s' % year)
	_met.output_metrics(ls)

	if ks != None:
		ks.update(_met.output_columns('fc%s' % year))

def cal_forest_change_agree_metric(f, tile, year1, year2, ls, ks):

	_met = forest_metrics(['FF', 'FN', 'NF', 'NN'])
	_convert_pos = lambda(lc): 0 if int(lc) == 1 else 1

	import csv_util
	for _r in csv_util.open(f):

		_v_ref1 = _r.get('f_y%s' % year1)
		_v_val1 = _r.get('f_f%s' % year1)

		_v_ref2 = _r.get('f_y%s' % year2)
		_v_val2 = _r.get('f_f%s' % year2)

		_b_val = _r.getint('f_valid')
		_v_wet = _r.getfloat('prob')
		_v_til = _r.get('tile')

		if _b_val == 0:
			continue

		if tile and _v_til != tile:
			continue

		_val_p1 = _convert_pos(_v_val1)
		_val_p2 = _convert_pos(_v_val2)

		_ref_p1 = _convert_pos(_v_ref1)
		_ref_p2 = _convert_pos(_v_ref2)

		_row = _val_p1 * 2 + _val_p2
		_col = _ref_p1 * 2 + _ref_p2

		_met.met_num[_row, _col] += 1
		_met.met_wet[_row, _col] += 1 / _v_wet

	_met.cal_sum_metrics()

	ls.append('')
	ls.append('> year %s - %s' % (year1, year2))
	_met.output_metrics(ls)

	if ks != None:
		ks.update(_met.output_columns('fcc%s' % year1))

def estimate_tiles(f_inp):
	import csv_util

	_ts = []

	for _l in csv_util.open(f_inp):
		_t = _l.get('tile')
		if _t not in _ts:
			_ts.append(_t)

	return _ts

def simplify_names(n):
	_n = n

	_n = _n.replace('fcc_', 'c')
	_n = _n.replace('fc_', 'f')
	_n = _n.replace('1990_', '90_')
	_n = _n.replace('2000_', '00_')
	_n = _n.replace('2005_', '05_')

	return _n

def main():
	_opts = _init_env()

	import os
	_years = [1990, 2000, 2005]

	_tiles = _opts.tile
	if _opts.auto_tile:
		if not _tiles:
			_tiles = estimate_tiles(_opts.input)
		print 'tile num:', len(_tiles)

		import progress_percentage
		_ppp = progress_percentage.progress_percentage(len(_tiles))

		os.path.exists(_opts.output) or os.makedirs(_opts.output)

		_ts = None
		_ss = []

		for _tile in _tiles:
			_ppp.next(count=True, message=_tile)

			_ks = {}
			_ls = []

			for _y in _years:
				cal_forest_agree_metric(_opts.input, _tile, _y, _ls, _ks)

			for _y in xrange(len(_years) - 1):
				cal_forest_change_agree_metric(_opts.input, _tile, _years[_y], _years[_y + 1], _ls, _ks)

			_f_out = os.path.join(_opts.output, '%s.txt' % _tile)
			with open(_f_out, 'w') as _fo:
				_fo.write('\n'.join(_ls))

			if _ts == None:
				_ts = sorted(_ks.keys())
				_ss.append(','.join(['tile'] + [simplify_names(_n) for _n in _ts]))
			_ss.append(','.join([_tile] + ['%s' % _ks[_k] for _k in _ts]))

		_ppp.done()

		_f_out = os.path.join(_opts.output, 'stat.csv')
		with open(_f_out, 'w') as _fo:
			_fo.write('\n'.join(_ss))
	else:

		_ks = {}
		_ls = []

		for _y in _years:
			cal_forest_agree_metric(_opts.input, _opts.tile, _y, _ls, _ks)

		for _y in xrange(len(_years) - 1):
			cal_forest_change_agree_metric(_opts.input, _opts.tile, _years[_y], _years[_y + 1], _ls, _ks)

		with open(_opts.output, 'w') as _fo:
			_fo.write('\n'.join(_ls))

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-t', '--tile', dest='tile')
	_p.add_argument('--auto-tile', dest='auto_tile', action='store_true')
	_p.add_argument('-o', '--output', dest='output', required=True)

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
