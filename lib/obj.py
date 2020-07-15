'''
File: obj.py
Author: Min Feng
Version: 0.1
Create: 2015-10-27 18:07:08
Description: class defined to facility object use
'''

# class obj(dict):
#
# 	def __init__(self, **w):
# 		super(obj, self).__init__(**w)
#
# 	def __getattr__(self, name):
# 		return super(obj, self).__getitem__(name)
#
# 	def __setattr__(self, name, value):
# 		return super(obj, self).__setitem__(name, value)
#
# 	def __str__(self):
# 		_ls = []
# 		for _k, _v in super(obj, self).items():
# 			_ls.append('%15s: %s' % (_k, _v))
# 		return '\n'.join(_ls)

class obj(object):

	def __init__(self, meta=None):
		self._meta = {} if not meta else meta

	def __getitem__(self, idx):
		from . import config
		if config.cfg.has_option('conf', 'debug') and config.cfg.getboolean('conf', 'debug'):
			import sys
			sys.stdout.write('[%s].' % idx)

		if idx not in self._meta:
			self._meta[idx] = obj()

		return self._meta[idx]

	def __setitem__(self, idx, val):
		from . import config
		if config.cfg.has_option('conf', 'debug') and config.cfg.getboolean('conf', 'debug'):
			print('[%s] = %s' % (idx, val))

		self._meta[idx] = val

	def __setattr__(self, name, val):
		if name.startswith('_'):
			return super(obj, self).__setattr__(name, val)
		return self.__setitem__(name, val)

	def __getattr__(self, name):
		if name.startswith('_'):
			return super(obj, self).__getattr__(name)
		return self.__getitem__(name)

	def _str(self, lev):
		if self._meta == None:
			return []

		assert isinstance(self._meta, dict)

		_ls = []
		for _k, _v in list(self._meta.items()):
			if isinstance(_v, obj):
				_ls.append('%s[%s]' % ('  ' * lev, _k))
				_ls.extend(_v._str(lev+1))
			else:
				_ls.append('%s%s=%s' % ('  ' * lev, _k, _v))

		return _ls

	def get(self, k, val=None):
		return self._meta.get(k, val)

	def getint(self, k, val=None):
		_v = self.get(k, val)
		if _v is None:
			return _v
		return int(_v)

	def getfloat(self, k, val=None):
		_v = self.get(k, val)
		if _v is None:
			return _v
		return float(_v)

	def save(self, f_out):
		import json
		with open(f_out, 'w') as _fo:
			_fo.write(json.dumps(self, indent=4, default=_convert))
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
		_obj = json.load(_fi, object_pairs_hook=_to_obj_ex)
		return _obj

def _to_obj_ex(v):
	_ds = {}
	for _k, _v in v:
		_ds[_k.strip()] = _v.strip if _v is str else _v

	return obj(_ds)

def _to_obj(o):
	if isinstance(o, dict):
		return obj(o)

	return o

def _convert(o):
	if isinstance(o, obj):
		return o._meta
	return o

def _object(o):
	if isinstance(o, dict):
		return obj(o)
	return o

from collections import defaultdict
def tree(): return defaultdict(tree)

