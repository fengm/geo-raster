
def estimate_type(vals):
	import re

	_vs = map(lambda x: x == '' or re.match('^-?[0-9]+$', x) != None, vals)
	if False not in _vs:
		return 'int', 4

	_vs = map(lambda x: x == '' or x == 'NaN' or \
			re.match('^-?\d*\.?\d+E-?\d+$', x) != None or \
			re.match('^-?\d*\.?\d+$', x) != None, vals)
	if False not in _vs:
		return 'float', 4

	_vs = map(lambda x: x == '' or re.match('^-?\d*\.?\d+E-?\d+$', x) != None, vals)
	if False not in _vs:
		return 'float', 4

	return 'string', max(map(len, vals))

def read(f, sep=','):
	_ls = [_l for _l in file(f).read().splitlines() if _l]

	_cols = _ls[0].split(sep)
	_vals = [_v for _v in [_l.split(sep) for _l in _ls[1:]] if len(_v) == len(_cols)]

	for _l in _ls[1:]:
		if len(_l.split(',')) != len(_cols):
			print '****', len(_l.split(',')), len(_cols), '|', _l

	_typs = []
	for i in xrange(len(_cols)):
		_typs.append(estimate_type([_v[i] for _v in _vals]))

	return _cols, _typs, _vals

class csv_class:

	def __init__(self, path, cols, sep):
		self.path = path
		self.cols = cols
		self.sep = sep

	def __str__(self):
		return self.sep.join(self.cols)

class csv_record:

	def __init__(self, info, line, vals):
		self.info = info
		self.line = line
		self.vals = vals

	def index(self, col):
		if col in self.info.cols:
			return self.info.cols.index(col)
		elif type(col) == int and col < len(self.vals):
			return col

		return -1

	def get(self, col):
		_idx = self.index(col)

		if _idx < 0:
			return None

		return self.vals[_idx]

	def getfloat(self, col):
		_v = self.get(col)
		if _v == None:
			return None
		return float(_v)

	def getint(self, col):
		_v = self.get(col)
		if _v == None:
			return None
		return int(_v)

	def set(self, col, val, style='%s'):
		_idx = self.index(col)

		if _idx < 0:
			raise Exception('column not found %s' % col)

		self.vals[_idx] = style % val

	def __str__(self):
		return self.info.sep.join(self.vals)

def open(f, sep=','):
	_cls = None
	with file(f) as _fi:
		_line = -1
		for _l in _fi:
			_l = _l.strip()

			if not _l:
				# skip empty lines
				continue

			_vs = _l.split(sep)

			if _cls == None:
				_cls = csv_class(f, _vs, sep)
			else:
				_line += 1

				if len(_vs) != len(_cls.cols):
					raise Exception('values (%s) does not match with the columns (%s)' % (len(_vs), len(_cls.cols)))

				yield csv_record(_cls, _line, _vs)

def parse_val(t, v):
	if t == 'int':
		return int(v)

	if t == 'float':
		return float(v)

	return v
