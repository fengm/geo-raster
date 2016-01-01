#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: convert_gz_tif.py
Author: Min Feng
Version: 0.1
Create: 2015-12-31 14:02:48
Description: convert gunzip images to internal compressed GTiff
'''

def convert(fi, fo):
	import os
	if os.path.exists(fo) and os.path.getsize(fo) > 0:
		return

	_d_out = os.path.dirname(fo)
	try:
		(lambda x: os.path.exists(x) or os.makedirs(x))(_d_out)
	except:
		pass

	import file_unzip
	with file_unzip.file_unzip() as _zip:
		_f = _zip.unzip(fi)

		_d_tmp = _zip.generate_file()
		os.makedirs(_d_tmp)

		import run_commands
		_c = 'gdalwarp -co "compress=lzw" %s %s' % (_f, os.path.join(_d_tmp, os.path.basename(fo)))
		if run_commands.run(_c)[0] != 0:
			import logging
			logging.error('failed to convert %s %s' % (fi, fo))
			raise Exception('failed to convert the file')

		file_unzip.compress_folder(_d_tmp, _d_out, [])

def check_image(f, p):
	return f.endswith(p)

def format_file(f, do, di=None):
	import os
	_f = os.path.basename(f)

	_do = do
	if di != None:
		_d = os.path.abspath(os.path.dirname(f))
		_do = os.path.join(_do, _d[len(os.path.abspath(di)) + 1:])

	return os.path.join(_do, _f[:-7] + '.tif')

def main():
	_opts = _init_env()

	_ps = []

	import os
	if os.path.isfile(_opts.input):
		if check_image(_opts.input, _opts.pattern):
			_ps.append((_opts.input, _opts.output))
		elif _opts.input.endswith('.txt'):
			with open(_opts.input) as _fi:
				for _f in _fi.read().splitlines():
					if _f:
						_ps.append((_f, format_file(_f, _opts.output)))
		else:
			raise Exception('does not support input file %s' % _opts.output)
	elif os.path.isdir(_opts.input):
		for _root, _dirs, _files in os.walk(_opts.input):
			for _file in _files:
				if check_image(_file, _opts.pattern):
					_f = os.path.join(_root, _file)
					_ps.append((_f, format_file(_f, _opts.output, _opts.input)))

	import multi_task
	multi_task.run(convert, multi_task.load(_ps, _opts), _opts)

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp', default='/export2/data/mfeng/tmp/convert')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('-p', '--pattern', dest='pattern', default='.img.gz')

	import multi_task
	multi_task.add_task_opts(_p)

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

	if not config.cfg.has_section('conf'):
		config.cfg.add_section('conf')

	for _k, _v in _opts.__dict__.items():
		if _v != None:
			config.cfg.set('conf', _k, str(_v))

	import file_unzip as fz
	fz.clean(fz.default_dir(_opts.temp))

	return _opts

if __name__ == '__main__':
	main()
