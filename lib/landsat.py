
'''Module for process Landsat file information'''

import re

band_vals = [1, 2, 3, 4, 5, 7]
band_txts = ['B', 'G', 'R', 'NIR', 'SWIR1', 'SWIR2']
band_l_rate = [0.659553184, 0.66026684, 0.659565581, 0.660032494, 0.660078238, 0.660153937]
band_h_rate = [1.516177958, 1.514539182, 1.516149462, 1.515076923, 1.514971928, 1.514798206]
band_gain_low = [[-6.2, 293.7], [-6.4, 300.9], [-5.0, 234.4], [-5.1, 241.1], [-1.0, 47.57], [-0.35, 16.54]]
band_gain_high = [[-6.2, 191.6], [-6.4, 196.5], [-5.0, 152.9], [-5.1, 157.4], [-1.0, 31.06], [-0.35, 10.80]]

class landsat_info:

	def __init__(self, sensor, tile, ac_date, full_name=None, note=None):
		self.sensor = sensor
		self.tile = tile
		self.ac_date = ac_date
		self.full_name = full_name
		self.note = note

		import datetime
		self.ac_date_obj = datetime.datetime.strptime(ac_date, '%Y%m%d')

	def __str__(self):
		return 'L%s_%s_%s' % (self.sensor, self.tile, self.ac_date)

def parse(code):
	_vs = parseLandsatId(code)
	if _vs == None:
		return None

	return landsat_info(_vs[0], _vs[1], _vs[2], code)

def band_to_text(b):
	if b not in band_vals:
		return ''

	return band_txts[band_vals.index(b)]

def parseLandsatId(id):
	_m = re.search('(p\d{3}r\d{3})_(\d)\w+(\d{8})', id)
	if _m:
		return int(_m.group(2)), _m.group(1), _m.group(3)

	_m = re.search('[lL](\d)_(p\d{3}r\d{3})_(\d{8})', id)
	if _m:
		return int(_m.group(1)), _m.group(2), _m.group(3)

	_m = re.search('L(\d)\d?(\d{3})(\d{3})_\d{3}(\d{8})', id)
	if _m:
		return int(_m.group(1)), 'p%sr%s' % (_m.group(2), _m.group(3)), _m.group(4)

	_m = re.search('LM(\d)(\d{3})(\d{3})(\d{7})', id)
	if _m:
		import datetime
		_date = datetime.datetime.strptime(_m.group(4), '%Y%j')
		return int(_m.group(1)), 'p%sr%s' % (_m.group(2), _m.group(3)), _date.strftime('%Y%m%d')

	_m = re.search('L\w(\d)(\d{3})(\d{3})(\d{4})(\d{3})', id)
	if _m:
		_year = int(_m.group(4))
		_day = int(_m.group(5))

		if _year < 1900:
			_year += 2000
			if _year > 2900:
				_year -= 1000
			if _year > 2070:
				_year -= 100

		# _year += 2000
		# if _year > 2070:
		# 	_year -= 100

		import datetime
		_date = datetime.datetime.strptime('%04d-%03d' % (_year, _day), '%Y-%j')

		return int(_m.group(1)), 'p%sr%s' % (_m.group(2), _m.group(3)), _date.strftime('%Y%m%d')

	return None

def parseLandsatCode(id):
	_m = re.search('p\d{3}r\d{3}_\d+\w+\d{8}', id)
	if _m:
		return _m.group()

	_m = re.search('L\d\d?\d{3}\d{3}_\d{3}\d{8}', id)
	if _m:
		return _m.group()

	_m = re.search('L\w(\d)(\d{3})(\d{3})(\d{4})(\d{3})', id)
	if _m:
		return _m.group()

	return None

def getSensorName(d):
	if d >= 7:
		return 'ETM+'
	elif d >= 4:
		return 'TM'
	else:
		return 'MSS'

def normalizeId(sensor, pathrow, date):
	return 'L%s_%s_%s' % (sensor, pathrow, date)

