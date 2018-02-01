'''
File: file_mag.py
Author: Min Feng
Version: 0.1
Create: 2017-12-10 17:13:23
Description:
'''

class obj_mag:

    def __init__(self):
        pass

    def put(self, f):
        raise NotImplementedError()

    def exists(self):
        raise NotImplementedError()

    def get(self):
        raise NotImplementedError()

class file_mag(obj_mag):

    def __init__(self, f):
        self._f = f
        obj_mag.__init__(self)

    def exists(self):
        import os
        return os.path.exists(self._f)

    def get(self):
        return self._f

    def put(self, f):
        import shutil
        shutil.move(f, self._f)

        if self._f.endswith('.shp') and f.endswith('.shp'):
            import os
            for _e in ['.prj', '.shx', '.dbf']:
                _f = f[:-4] + _e
                if os.path.exists(_f):
                    shutil.copy(_f, self._f[:-4] + _e)

    def __str__(self):
        return self._f

class s3_mag(obj_mag):

    def __init__(self, f):
        import re

        _m = re.match('s3://([^/]+)/(.+)', f)
        if _m is None:
            raise Exception('failed to parse S3 file %s' % f)

        _bucket = _m.group(1)
        _path = _m.group(2)

        from gio import cache_mag
        _s3 = cache_mag.s3(_bucket)

        self._bucket = _bucket
        self._path = _path

        self._f = f
        self._s3 = _s3

        obj_mag.__init__(self)

    def exists(self):
        return self._s3.get_key(self._path) is not None

    def get(self):
        _o = self._s3.get(self._path)
        if _o:
            if self._path.endswith('.shp'):
                for _e in ['.prj', '.shx', '.dbf']:
                    self._s3.get(self._path[:-4] + _e)
        return _o

    def put(self, f, update=False):
        self._s3.put(self._path, f, update=update)

        if self._path.endswith('.shp') and f.endswith('.shp'):
            import os
            for _e in ['.prj', '.shx', '.dbf']:
                _f = f[:-4] + _e
                if os.path.exists(_f):
                    self._s3.put(self._path[:-4] + _e, _f)

    def __str__(self):
        return self._f

def get(f):
    if f.startswith('s3://'):
        return s3_mag(f)

    return file_mag(f)

