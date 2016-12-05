
import setuptools
from Cython.Distutils import build_ext
import os

_ms = []
for _root, _dirs, _files in os.walk('mod'):
	for _file in _files:
		if _file.endswith('.pyx'):
			_f, _e = os.path.splitext(_file)

			_n = _f
			if _n.endswith('_c'):
				_n = _n[:-2]

			_ms.append(setuptools.Extension("gio.%s" % _n, [os.path.join(_root, _file)],
				#extra_compile_args=["-O3", "-ffast-math","-funroll-loops"],
				define_macros=[("NPY_NO_DEPRECATED_API", None)]))

_ss = []
for _root, _dirs, _files in os.walk('util'):
	for _file in _files:
		if not _file.endswith('.py'):
			continue

		_f = os.path.join(_root, _file)
		_ss.append(_f)

setuptools.setup(name='geo-raster', version='1.0', description='', \
		author='Min Feng', author_email='mfeng.geo@gmail.com', \
		# packages=['gio', 'gio/data/landsat'],
		# package_dir={'gio': 'lib', 'gio/data/landsat': 'lib/data/landsat'},
		# package_data={'gio/data/landsat': ['lib/data/landsat/*']},
		packages=['gio'],
		package_dir={'gio': 'lib'},
		include_package_data=True,
		cmdclass = {"build_ext": build_ext},
		ext_modules=_ms,
		scripts=_ss,
		)

