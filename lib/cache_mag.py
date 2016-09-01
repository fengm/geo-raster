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

	def cached(self, key):
		_f = self.path(key)
		import os
		return os.path.exists(_f) and os.path.getsize(_f) > 0

	def _format_str(self, t):
		import re
		_k = list(re.sub('[^\w\d_]', '_', t))

		for i in xrange(len(_k)):
			if t[i] in ['\\', '/', '.', '-']:
				_k[i] = t[i]

		return ''.join(_k)

	def path(self, key):
		import os
		return os.path.join(self._d, self._t, self._format_str(key))

	def get(self, key):
		if not self.cached(key):
			return None

		return self.path(key)

	def put(self, key, inp):
		_f = self.path(key)

		if self.cached(key):
			return _f

		import os
		try:
			(lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))
		except Exception:
			pass

		import shutil
		shutil.copy(inp, _f)

		return _f

class s3():
	"""manage Landsat cache files"""

	def __init__(self, bucket):
		self._t = bucket
		self._c = cache_mag(bucket)
		self.bucket = self._bucket()

	def _bucket(self):
		import boto

		_s3 = boto.connect_s3()
		_bk = _s3.get_bucket(self._t)

		return _bk

	def get(self, key):
		_f = self._c.path(key.key)

		if self._c.cached(key.key):
			return _f

		import os
		try:
			(lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))
		except Exception:
			pass

		_t = _f + '.bak'
		with open(_t, 'wb') as _fo:
			self.bucket.get_key(key).get_contents_to_file(_fo)

		import shutil
		shutil.move(_t, _f)

		return _f

