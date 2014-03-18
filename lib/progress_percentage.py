
'''
File: progress_percentage.py
Author: Min Feng
Version: 0.1
Create: 2012-03-08 14:41:34
Description: Show progress in percentage
'''
'''
Version: 0.2
Date: 2012-06-25 14:41:27
Note: Option for showing the progress bar
'''
import datetime, logging, sys

show=True

class progress_percentage:

	def __init__(self, size, title=None, step=100, txt_format='%(p)3d%%', bar=False):
		self.pos = -1
		self.cur = -1
		self.size = size
		self.step = step
		self.txt_format = txt_format
		self.time_s = datetime.datetime.now()
		self.title = title
		self.bar = bar

		logging.debug('+ start process :' + title if title != None \
				else '<no name>')
		if title != None:
			print '>', title

	def print_prog(self, pos):
		if not show:
			return

		_pos = pos if pos <= 100 else 100
		print '\r',

		if self.bar:
			_len_l = _pos / 2
			if _len_l == 0:
				_len_l = 1
			_len_r = 100 / 2 - _len_l

			_txt = ''
			_txt += '=' * (_len_l - 1)
			_txt += '>'
			_txt += '-' * _len_r
			print _txt,

		print self.txt_format % {'p': _pos},
		print '(%s)' % (datetime.datetime.now() - self.time_s),
		sys.stdout.flush()

	def next(self, step=1, count=False, message=None):
		self.cur += step

		if count:
			if show:
				print '\r %s/%s: %s' % (self.cur, self.size, message if message else ''),
				print '(%s)' % (datetime.datetime.now() - self.time_s), ' ',
				import sys
				sys.stdout.flush()
		else:
			_pos = self.cur * self.step // self.size

			if self.pos != _pos:
				self.pos = _pos
				self.print_prog(self.pos * 100 / self.step)

	def done(self, format_end='\r%(p)3d%% | duration: %(time_duration)s'):
		self.print_prog(100)
		if show:
			print ''

		self.time_e = datetime.datetime.now()
		_d = self.time_e - self.time_s

		logging.debug('- end process ' + format_end % {'p': 100, 'time_duration': _d, 'time_start': self.time_s, 'time_end': self.time_e})

