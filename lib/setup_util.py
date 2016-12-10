'''
File: setup_util.py
Author: Min Feng
Version: 0.1
Create: 2016-12-10 14:47:36
Description: help running setup.py
'''

def init(tag):
	import setuptools
	from Cython.Distutils import build_ext
	import os

	_package = tag

	# import sys
	# _path = lambda x: os.path.join(sys.path[0], x)
	_path = lambda x: x

	_ms = []
	for _root, _dirs, _files in os.walk(_path('mod')):
		for _file in _files:
			if _file.endswith('.pyx'):
				_f, _e = os.path.splitext(_file)

				_n = _f
				if _n.endswith('_c'):
					_n = _n[:-2]

				_ms.append(setuptools.Extension(_package + ".%s" % _n, [os.path.join(_root, _file)],
					#extra_compile_args=["-O3", "-ffast-math","-funroll-loops"],
					define_macros=[("NPY_NO_DEPRECATED_API", None)]))

	_ss = []
	for _bin in ['util', 'bin']:
		for _root, _dirs, _files in os.walk(_path(_bin)):
			for _file in _files:
				if os.path.splitext(_file)[-1] not in ['.py']:
					continue

				_f = os.path.join(_root, _file)
				_ss.append(_f)

	setuptools.setup(name=_package, version='1.0', description='', \
			author='Min Feng', author_email='mfeng.geo@gmail.com', \
			# packages=[_package, 'gio/data/landsat'],
			# package_dir={_package: 'lib', 'gio/data/landsat': 'lib/data/landsat'},
			packages=[_package],
			package_dir={_package: 'lib'},
			# package_data={_package: ['etc/*']},
			# include_package_data=True,
			cmdclass = {"build_ext": build_ext},
			ext_modules=_ms,
			scripts=_ss,
			)

	if os.path.exists(_path('etc')):
		import os
		if 'G_INI' in os.environ and (os.environ['G_INI']):
			print ' == copying config file =='
			_d_ini = os.environ['G_INI']
			if not os.path.exists(_d_ini):
				os.makedirs(_d_ini)

			import shutil
			for _f in os.listdir(_path('etc')):
				print ' + copy config file', os.path.join(_d_ini, _f)
				shutil.copy(os.path.join('etc', _f), os.path.join(_d_ini, _f))

