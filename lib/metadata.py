'''
File: metadata.py
Author: Min Feng
Version: 0.1
Create: 2015-07-28 18:30:01
Description:
'''

class metadata:

	def __init__(self):
		import collections
		self._meta = collections.OrderedDict()

	def __getitem__(self, idx):
		import config
		if config.cfg.has_option('conf', 'debug') and config.cfg.getboolean('conf', 'debug'):
			import sys
			sys.stdout.write('[%s].' % idx)

		if idx not in self._meta:
			self._meta[idx] = metadata()

		return self._meta[idx]

	def __setitem__(self, idx, val):
		import config
		if config.cfg.has_option('conf', 'debug') and config.cfg.getboolean('conf', 'debug'):
			print '[%s] = %s' % (idx, val)

		self._meta[idx] = val

	def _str(self, lev):
		if self._meta == None:
			return []

		assert isinstance(self._meta, dict)

		_ls = []
		for _k, _v in self._meta.items():
			if isinstance(_v, metadata):
				_ls.append('%s[%s]' % ('  ' * lev, _k))
				_ls.extend(_v._str(lev+1))
			else:
				_ls.append('%s%s=%s' % ('  ' * lev, _k, _v))

		return _ls

	def save(self, f_out):
		_ls = self._str(0)

		with open(f_out, 'w') as _fo:
			_fo.write('\n'.join(_ls))

def main():
	_opts = _init_env()

	_m = metadata()
	_m['name'] = 'mfeng'
	_m['test1']['test2'] = 23
	_m['test1']['test3'] = 22
	_m['test1']['test4'] = 'test'
	_m['test1']['test5']['test2'] = 'test'

	_m.save('test1.txt')

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')
	_p.add_argument('--temp', dest='temp')

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

