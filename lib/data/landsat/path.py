

def path(tag=None):
	import os

	if tag == 'wrs1':
		_f = os.path.join(os.path.dirname(__file__), 'wrs1_descending.shp')
		if os.path.exists(_f):
			return _f

		raise Exception('failed to find file %s' % _f)
	else:
		_f = os.path.join(os.path.dirname(__file__), 'wrs2_descending.shp')
		if os.path.exists(_f):
			return _f

		raise Exception('failed to find file %s' % _f)

