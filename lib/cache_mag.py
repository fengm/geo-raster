'''
File: cache_mag.py
Author: Min Feng
Version: 0.1
Create: 2016-05-11 15:25:43
Description: manage Landsat cache files
'''

import logging

class file_obj():

	def __init__(self, f):
		import os

		self._f = f
		self._t = os.path.getatime(f)
		self._z = os.path.getsize(f)

	def __cmp__(self, f):
		return cmp(self._t, f._t)

class cache_mag():
	"""manage Landsat cache files"""

	def __init__(self, tag, cache=None):
		import config

		self._t = tag
		self._d = cache if cache else config.get('conf', 'cache')
		self._n = 0

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

		_p = self._format_str(key)
		if _p and _p[0] in ['/', '\\']:
			# remove the root path if it exists
			_p = _p[1:]

		return os.path.join(self._d, self._t, _p)

	def get(self, key):
		if not self.cached(key):
			return None

		return self.path(key)

	def put(self, key, inp=None, replace=True):
		import os

		_f = self.path(key)
		_inp = inp if inp else key

		if self.cached(key):
			if replace:
				logging.info('clear cached %s' % key)
				os.remove(_f)
			else:
				logging.info('loading cached %s' % key)
				return _f

		try:
			(lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))
		except Exception:
			pass

		import random
		_f_out = _f + str(random.randint(0, 1000)) + '.bak'

		import shutil
		shutil.copy(_inp, _f_out)

		if os.path.exists(_f) == False:
			shutil.move(_f_out, _f)
		else:
			os.remove(_f_out)

		self._clean()

		return _f

	def _clean_file(self, f):
		try:
			import os
			os.remove(f._f)
			logging.info('clean cached file %s' % f._f)
		except Exception, err:
			import traceback

			logging.error(traceback.format_exc())
			logging.error(str(err))

			print '\n\n* Error:', err

	def _clean(self):
		import os

		self._n += 1
		if self._n < 1000:
			return
		self._n = 0

		from gio import config
		_max_file = config.getint('conf', 'max_cached_file', -1)
		_max_size = config.getfloat('conf', 'max_cached_size', -1)

		if _max_file < 0 and _max_size < 0:
			return

		_fs = []
		_sz = 0.0
		for _root, _dirs, _files in os.walk(self._d):
			for _file in _files:
				_ff = os.path.join(_root, _file)
				if _file.endswith('.bak'):
					import time
					# remove bak files that has not been used for 24 hours
					if (time.time() - os.path.getatime(_ff)) > 60 * 60 * 24:
						logging.warning('remove bak file %s' % _ff)
						os.remove(_ff)
					continue

				_fs.append(file_obj(_ff))
				_sz += os.path.getsize(_ff)

		_fs = sorted(_fs)

		logging.info('checking cache %s, %s (%s, %s)' % (len(_fs), _sz, _max_file, _max_size))

		_fd1 = []
		if _max_file > 0 and len(_fs) > _max_file:
			_fd = _fs[:_max_file-len(_fs)]

		_fd2 = []
		if _max_size > 0:
			# convert from GB
			_max_size *= (1024 * 1024 * 1024)

		if _max_size > 0 and _sz > _max_size:
			_zz = _sz
			for _f in _fs:
				_fd2.append(_f)
				_zz -= _f._z

				if _zz <= _max_size:
					break

		_fd = _fd1 if len(_fd1) > len(_fd2) else _fd2
		logging.info('identified cached files to clean %s %s %s' % (len(_fd), len(_fd1), len(_fd2)))

		for _f in _fd:
			self._clean_file(_f)

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

	def get(self, key, lock=None):
		_f = self._c.path(key.key)

		if self._c.cached(key.key):
			return _f

		import os
		try:
			(lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))
		except Exception:
			pass

		import shutil
		import file_unzip

		for _i in xrange(3):
			_t = file_unzip.generate_file(os.path.dirname(_f), '', '.bak')

			try:
				# write an empty file to prevent other process to use the same file name
				with open(_t, 'wb') as _fo:
					_fo.write('')

				with open(_t, 'wb') as _fo:
					self.bucket.get_key(key).get_contents_to_file(_fo)
					if os.path.exists(_t) and os.path.getsize(_t) > 0:
						if lock is None:
							if os.path.exists(_f) == False:
								shutil.move(_t, _f)
						else:
							with lock:
								if os.path.exists(_f) == False:
									shutil.move(_t, _f)

						return _f
			finally:
				if os.path.exists(_t):
					os.remove(_t)

		raise Exception('failed to load S3 file %s' % key)

