'''
File: obj.py
Author: Min Feng
Version: 0.1
Create: 2015-10-27 18:07:08
Description: class defined to facility object use
'''

class obj(dict):

	def __init__(self, **w):
		super(obj, self).__init__(**w)

	def __getattr__(self, name):
		return super(obj, self).__getitem__(name)

	def __setattr__(self, name, value):
		return super(obj, self).__setitem__(name, value)

	def __str__(self):
		_ls = []
		for _k, _v in self._obj.items():
			_ls.append('%15s: %s' % (_k, _v))
		return '\n'.join(_ls)
