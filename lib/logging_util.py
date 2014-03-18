
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
	_f = f
	if not _f:
		import sys, os, re

		_d_log = os.path.join(sys.path[0], 'log')
		os.path.exists(_d_log) or os.makedirs(_d_log)

		_f = os.path.basename(sys.argv[0])
		_m = re.match('(.+)\.[^\.]+$', _f)
		if _m:
			_f = _m.group(1)

		# import datetime
		# _f += '_%s.log' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

		_f = os.path.join(_d_log, _f + '.log')

	# print 'logging file', _f
	_handler = sync_file_log_handler(_f)
	_handler.setLevel(logging.DEBUG)
	_handler.setFormatter(logging.Formatter('%(process)d:%(asctime)-15s:%(levelname)s:%(message)s'))

	_log = logging.getLogger()
	_log.addHandler(_handler)
	_log.setLevel(logging.INFO)

	# logging.basicConfig(filename=_f, level=logging.DEBUG, filemode=filemode, format=format)

