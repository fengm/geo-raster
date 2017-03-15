'''
File: logging_util.py
Author: Min Feng
Version: 0.1
Create: 2013-06-14 15:11:29
Description: initilize the logging module
'''

import logging

class sync_file_log_handler(logging.FileHandler):

	def __init__(self, filename, mode='a', encoding=None):
		import multiprocessing
		self.p_lock = multiprocessing.Lock()
		import threading
		self.t_lock = threading.Lock()

		logging.FileHandler.__init__(self, filename, mode=mode, encoding=encoding)

	def emit(self, record):
		with self.p_lock:
			with self.t_lock:
				logging.FileHandler.emit(self, record)

def init(f=None):
	import sys, os, re

	_f = f
	if not _f:
		_f = os.path.basename(sys.argv[0])
		_m = re.match('(.+)\.[^\.]+$', _f)
		if _m:
			_f = _m.group(1)

		# import datetime
		# _f += '_%s.log' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

		if 'G_LOG' in os.environ:
			_f = os.path.join(os.environ['G_LOG'], _f + '.log')
		else:
			_f = os.path.join(sys.path[0], 'log', _f + '.log')

	_d_log = os.path.dirname(_f)
	os.path.exists(_d_log) or os.makedirs(_d_log)

	import config
	_debug = config.getboolean('conf', 'debug') if config.cfg else False
	if _debug:
		print ' - debugging'
		print ' - log file', _f

	# print 'logging file', _f
	_handler = sync_file_log_handler(_f)
	_level = logging.DEBUG # if _debug else logging.INFO

	_handler.setLevel(_level)
	if _debug:
		_handler.setFormatter(logging.Formatter('%(process)d:%(asctime)-15s:%(levelname)s:%(message)s'))
	else:
		_handler.setFormatter(logging.Formatter('%(process)d:%(asctime)-15s:%(levelname)s:%(message)s'))
		# _handler.setFormatter(logging.Formatter('%(process)d:%(levelname)s:%(message)s'))

	_log = logging.getLogger()
	_log.addHandler(_handler)

	_level = logging.INFO if _debug else logging.WARNING
	_log.setLevel(_level)

	# logging.basicConfig(filename=_f, level=logging.DEBUG, filemode=filemode, format=format)

