'''
File: cache_mag.py
Author: Min Feng
Version: 0.1
Create: 2016-05-11 15:25:43
Description: manage Landsat cache files
'''

class cache_mag():
	"""manage Landsat cache files"""

	def __init__(self, tag):
		import config

		self._t = tag
		self._d = config.get('conf', 'cache')

	def path(self, lid):
		import os
		return os.path.join(self._d, lid.tile, '%s_%s.tif' % (lid, self._t))

	def has_id(self, lid):
		import os
		return os.path.exists(self.path(lid))

	def cache(self, lid, f):
		_f = self.path(lid)

		import os
		(lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))

		import shutil
		shutil.copy(f, _f)

		return _f

