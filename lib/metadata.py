'''
File: metadata.py
Author: Min Feng
Version: 0.1
Create: 2015-07-28 18:30:01
Description:
'''

class metadata(object):

	def __init__(self, meta=None):
		import collections
		self._meta = collections.OrderedDict() if not meta else meta

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

	def __setattr__(self, name, val):
		if name.startswith('_'):
			return super(metadata, self).__setattr__(name, val)
		return self.__setitem__(name, val)

	def __getattr__(self, name):
		if name.startswith('_'):
			return super(metadata, self).__getattr__(name)
		return self.__getitem__(name)

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
		import json
		with open(f_out, 'w') as _fo:
			_fo.write(json.dumps(self, indent=4, ensure_ascii=False, default=_convert))
			# _fo.write(json.dumps(self, indent=4, default=_convert))
		return

	def save_txt(self, f_out):
		'''save to a customized format'''
		_ls = self._str(0)

		with open(f_out, 'w') as _fo:
			_fo.write('\n'.join(_ls))

	def __str__(self):
		return '\n'.join(self._str(0))

def load(f):
	with open(f) as _fi:
		import json
		# import collections
		# _obj = json.load(_fi, object_hook=_to_obj, object_pairs_hook=collections.OrderedDict)
		_obj = json.load(_fi, object_pairs_hook=_to_obj_ex)
		return _obj

def _to_obj_ex(v):
	import collections
	_ds = collections.OrderedDict()

	for _k, _v in v:
		_ds[_k.strip()] = _v.strip if _v is str else _v

	return metadata(_ds)

def _to_obj(obj):
	if isinstance(obj, dict):
		return metadata(obj)

	return obj

def _convert(obj):
	if isinstance(obj, metadata):
		return obj._meta
	return obj

def _object(obj):
	if isinstance(obj, dict):
		return metadata(obj)
	return obj

def main():
	_m = metadata()
	_m['name'] = 'mfeng'
	_m['test1']['test2'] = 23
	_m['test1']['test3'] = 22
	_m['test1']['test4'] = 'test'
	_m['test1']['test5']['test2'] = 'test'
	_m.test2.test3 = 'tttt'

	_m.save('test1.txt')

	_m = load('test1.txt')
	print _m.test1.test4
	print _m['test1']['test4']
	print _m

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

