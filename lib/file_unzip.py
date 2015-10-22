'''
File: file_unzip.py
Author: Min Feng
Version: 0.1
Create: 2012-05-30 18:42:22
Description: utility library for compress/uncompress file/folder
'''

_block_size = 1024 * 1024

import logging

def uncompress_file(f, d_ot):
	import gzip
	import os

	_fo = d_ot
	if os.path.isdir(d_ot):
		_fo = os.path.join(d_ot, os.path.basename(f)[:-3])
	else:
		# skip if the file is already unzipped
		if os.path.exists(_fo) and os.path.getsize(_fo) > 0:
			return

		_do = os.path.dirname(_fo)
		if _do:
			os.path.exists(_do) or os.makedirs(_do)

	_ft = _fo + '.tmp'

	logging.info('unzipping %s: %s' % (f, _ft))
	try:
		with gzip.open(f, 'rb') as _f_in:
			with open(_ft, 'wb') as _f_ot:
				while True:
					_dat = _f_in.read(_block_size)
					if not _dat:
						break
					_f_ot.write(_dat)
				_f_ot.flush()

			import shutil
			shutil.move(_ft, _fo)
	except BaseException, err:
		os.path.exists(_ft) and os.remove(_ft)
		raise err

def uncompress_folder(d_in, d_ot):
	import os, shutil

	# create the folder for output
	os.path.exists(d_ot) or os.makedirs(d_ot)

	for _f in os.listdir(d_in):
		_ff = os.path.join(d_in, _f)

		# process folder
		if os.path.isdir(_ff):
			uncompress_folder(_ff, os.path.join(d_ot, _f))
			continue

		# process file
		if _f.endswith('.gz'):
			uncompress_file(_ff, d_ot)
		else:
			shutil.copy(_ff, d_ot)

def compress_file(f_src, f_dst=None, remove_src=True):
	import gzip
	import os

	_f_dst = f_dst
	if not _f_dst:
		_f_dst = os.path.dirname(f_src)
		if not _f_dst:
			_f_dst = '.'

	if os.path.isdir(_f_dst):
		_f_dst = os.path.join(_f_dst, os.path.basename(f_src) + '.gz')

	_f_tmp = _f_dst + '.tmp'
	try:
		logging.info('compress %s to %s' % (f_src, _f_dst))
		with open(f_src, 'rb') as _zip_src:
			with open(_f_tmp, 'wb') as _ft:
				with gzip.GzipFile(_f_dst, 'wb', fileobj=_ft) as _zip_tar:
					while True:
						_dat = _zip_src.read(_block_size)
						if not _dat:
							break
						_zip_tar.write(_dat)
					_zip_tar.flush()

				import time
				time.sleep(0.1)
				_ft.flush()

		# import time
		# time.sleep(1)

		import shutil
		shutil.move(_f_tmp, _f_dst)

		if remove_src:
			os.remove(f_src)
	except BaseException, err:
		import os
		os.path.exists(_f_tmp) and os.remove(_f_tmp)

		raise err

def check_prefix(f, exts):
	if not f:
		return False

	if exts == None:
		return True

	for _ext in exts:
		if f.endswith(_ext):
			return True

	return False

def compress_folder(fd_in, fd_ot, compress_exts=None, exclude_exts=None):
	'''compress files in the folder to the target folder'''
	import shutil
	import os

	logging.debug('compress results from %s to %s' % (fd_in, fd_ot))
	os.path.exists(fd_ot) or os.makedirs(fd_ot)

	for _file in os.listdir(fd_in):
		_ff = os.path.join(fd_in, _file)

		# process folder
		if os.path.isdir(_ff):
			compress_folder(_ff, os.path.join(fd_ot, _ff), compress_exts)
			continue

		# process file
		_f_in = _ff
		_f_ot = os.path.join(fd_ot, _file)

		if exclude_exts and check_prefix(_file, exclude_exts):
			continue

		if check_prefix(_file, compress_exts):
			_f_ot = _f_ot + '.gz'
			logging.debug('zipping %s to %s' %(_f_in, _f_ot))
			compress_file(_f_in, _f_ot)
		else:
			logging.debug('copying %s to %s' %(_f_in, _f_ot))
			shutil.copy(_f_in, _f_ot)

def generate_id(fd_out, prefix='', subfix=''):
	import random, os

	_id = [''] * 10
	for i in xrange(len(_id)):
		_id[i] = chr(int(random.random() * 26) + 97)

	_id = ''.join(_id)
	_id = '%s%s%s' % (prefix, _id, subfix)

	if fd_out and os.path.exists(os.path.join(fd_out, _id)):
		return generate_id(fd_out, prefix, subfix)

	return _id

def generate_file(fd_out, prefix='', subfix=''):
	if fd_out == None:
		raise Exception('invalid path parameter')

	import os
	return os.path.join(fd_out, generate_id(fd_out, prefix, subfix))

def default_dir(fd_out):
	import os, sys

	# use 'tmp' folder at the root of the code when no folder specified
	if fd_out:
		return fd_out

	import config
	if config.cfg.has_option('conf', 'temp'):
		return config.cfg.get('conf', 'temp')

	return os.path.join(sys.path[0], 'tmp')

def clean(fd_out, remove_root=False):
	'''force to clean the folder'''
	import shutil, os

	logging.warning('clean folder: %s (%s)' % (fd_out, remove_root))
	if remove_root:
		shutil.rmtree(fd_out, True)
		return

	for _root, _dirs, _files in os.walk(fd_out):
		for _file in _files:
			try:
				os.remove(os.path.join(_root, _file))
			except Exception:
				# ignore the errors
				pass
		for _dir in _dirs:
			shutil.rmtree(os.path.join(_root, _dir), True)

class file_unzip:
	def __init__(self, fd_out='', exclusive=True, debug=False):
		import os

		_fd_out = default_dir(fd_out)

		self.pfolder = _fd_out
		self.existed = os.path.exists(_fd_out)

		_fd_out = generate_file(_fd_out)
		os.makedirs(_fd_out)

		self.fd_out = _fd_out
		self.files = []
		self.exclusive = exclusive
		self._debug = debug

		logging.info('temp: %s' % self.fd_out)
		if self._debug:
			print 'temp:', self.fd_out

	# support with statement
	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		if self._debug:
			logging.info('remain the temporary files in debug mode')
		else:
			self.clean()

	def generate_file(self, prefix='', subfix=''):
		return generate_file(self.fd_out, prefix, subfix)

	def _estimate_output(self, f, reuse):
		import os
		_f_out = os.path.join(self.fd_out, os.path.basename(f)[:-3])

		if not os.path.exists(_f_out) or reuse:
			return _f_out

		for i in xrange(10000000):
			_d_out = os.path.join(self.fd_out, 'a%07d' % i)
			if os.path.exists(_d_out):
				continue
			return os.path.join(_d_out, os.path.basename(f)[:-3])

		raise Exception('failed to estimate output file name')

	def unzip(self, f, f_out=None, reuse=False):
		import sys, logging

		if f.lower()[-3:] != '.gz':
			return f

		logging.info('> unzip ' + f)
		sys.stdout.flush()

		_f_out = f_out
		if not _f_out:
			_f_out = self._estimate_output(f, reuse)

		uncompress_file(f, _f_out)

		if not f_out and (_f_out not in self.files):
			self.files.append(_f_out)

		return _f_out

	def clean(self):
		import shutil, os

		if self.exclusive:
			# shutil.rmtree(self.fd_out if self.existed else self.pfolder, True)
			# forbidden the code for removing the parent dir because it may cause
			#  potential issue for multiple processing, Min, 13/03/03
			shutil.rmtree(self.fd_out, True)
			self.files = []
			return

		for _f in self.files:
			os.remove(_f)
		self.files = []
		return

