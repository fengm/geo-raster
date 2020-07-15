'''
File: setup_util.py
Author: Min Feng
Version: 0.1
Create: 2016-12-10 14:47:36
Description: help running setup.py
'''

def _parse_opts():
    import sys
    
    _as = sys.argv
    
    _ps = {}
    _pp = ['--overwrite-config']
    for _p in _pp:
        _ps[_p] = _p in _as
    
    sys.argv = [_p for _p in _as if _p not in _pp]
    return _ps

def init(tag, version=1.0, requires=[], author='Min Feng', email='mfeng.geo@gmail.com'):
    import setuptools
    # from Cython.Distutils import build_ext
    from setuptools.command.build_ext import build_ext
    import os
    import numpy

    _package = tag
    _opts = _parse_opts()

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
                    define_macros=[("NPY_NO_DEPRECATED_API", None)],
                    include_dirs=[numpy.get_include()]))

    _ss = []
    for _bin in ['util', 'bin']:
        for _root, _dirs, _files in os.walk(_path(_bin)):
            for _file in _files:
                if os.path.splitext(_file)[-1] not in ['.py']:
                    continue

                _f = os.path.join(_root, _file)
                _ss.append(_f)

    _ds = {}
    _ps = []

    if os.path.exists('lib'):
        _ps.append(_package)
        _ds[_package] = 'lib'

    setuptools.setup(name=_package, version=version, description='', \
            author=author, author_email=email, \
            packages=_ps,
            package_dir=_ds,
            # package_data={_package: ['etc/*']},
            # include_package_data=True,
            cmdclass = {"build_ext": build_ext},
    		install_requires=requires,
            ext_modules=_ms,
            scripts=_ss,
            )

    if os.path.exists(_path('etc')):
        import os
        import shutil

        if 'G_INI' in os.environ and (os.environ['G_INI']):
            print(' == copying config file ==')
            _d_ini = os.environ['G_INI']
            if not os.path.exists(_d_ini):
                os.makedirs(_d_ini)

            for _root, _dirs, _files in os.walk(_path('etc')):
                for _file in _files:
                    _f_inp = os.path.join(_root, _file)
                    _f_out = os.path.join(_root.replace(_path('etc'), _d_ini), _file)

                    if not _opts['--overwrite-config'] and os.path.exists(_f_out):
                        print(' - skip existed config file', _file)
                        continue

                    _d_out = os.path.dirname(_f_out)
                    os.path.exists(_d_out) or os.makedirs(_d_out)

                    print(' + copy config file', _f_out)
                    shutil.copy2(_f_inp, _f_out)

