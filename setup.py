
import setuptools
# from Cython.Distutils import build_ext
from setuptools.command.build_ext import build_ext
import os
import numpy

def _walk_files(d, fs):
    for _f in os.listdir(d):
        if _f.startswith('.'):
            continue
            
        _a = os.path.join(d, _f)
        if os.path.isdir(_a):
            _walk_files(_a, fs)
            continue
            
        fs.append((d, _f))
        
def walk_files(d):
    _fs = []
    _walk_files(d, _fs)
    return _fs

_ms = []

for _root, _file in walk_files('mod'):
    if not _file.endswith('.pyx'):
        continue
        
    _f, _e = os.path.splitext(_file)

    _n = _f
    if _n.endswith('_c'):
        _n = _n[:-2]

    _ms.append(setuptools.Extension("gio.%s" % _n, [os.path.join(_root, _file)],
        #extra_compile_args=["-O3", "-ffast-math","-funroll-loops"],
        define_macros=[("NPY_NO_DEPRECATED_API", None)], 
        include_dirs=[numpy.get_include()]))

_ss = []

for _root, _file in walk_files('util'):
    if not _file.endswith('.py'):
        continue

    _f = os.path.join(_root, _file)
    _ss.append(_f)

_exts = []
if _ms:
    _exts = _ms
    # from Cython.Build import cythonize
    # _exts = cythonize(_ms, compiler_directives={'language_level': 3})
    # _exts = cythonize(_ms, compiler_directives={'language_level': 3, 'boundscheck': False, 'wraparound': False})
        
setuptools.setup(name='geo-raster', version='2.3.0', description='', \
        author='Min Feng', author_email='mfeng.geo@gmail.com', \
        # packages=['gio', 'gio/data/landsat'],
        # package_dir={'gio': 'lib', 'gio/data/landsat': 'lib/data/landsat'},
        packages=['gio'],
        package_dir={'gio': 'lib'},
        include_package_data=True,
        install_requires=['awscli', 'boto3', 'cython', 'numpy', 'pandas', 'psycopg2', 'pillow'],
        cmdclass = {"build_ext": build_ext},
        ext_modules=_exts,
        scripts=_ss
        )

