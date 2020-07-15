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

    def list(self, recursive=False):
        raise NotImplementedError()
        
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass
        
class file_mag(obj_mag):

    def __init__(self, f):
        self._f = f
        obj_mag.__init__(self)

    def exists(self):
        if not self._f:
            return False
            
        import os
        return os.path.exists(self._f)

    def get(self):
        return self._f

    def put(self, f):
        import os
        (lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(self._f))

        import shutil
        shutil.copy(f, self._f)

        if self._f.endswith('.shp') and f.endswith('.shp'):
            import os
            for _e in ['.prj', '.shx', '.dbf']:
                _f = f[:-4] + _e
                if os.path.exists(_f):
                    shutil.copy(_f, self._f[:-4] + _e)
                    
    def list(self, recursive=False):
        import os
        if not os.path.exists(self._f):
            return []

        if os.path.isfile(self._f):
            return [file_mag(self._f)]
            
        if recursive:
            _fs = []
            
            for _root, _dirs, _files in os.walk(str(self._f)):
                for _f in _files:
                    _fs.append(file_mag(os.path.join(_root, _f)))
            
            return _fs

        _fs = [file_mag(os.path.join(self._f, _f)) for _f in os.listdir(self._f)]
        return _fs

    def __str__(self):
        return self._f

class s3_mag(obj_mag):

    def __init__(self, f, s3=None):
        import re
        
        _m = re.match('s3://([^/]+)/(.+)', f)
        if _m is None:
            raise Exception('failed to parse S3 file %s' % f)

        _bucket = _m.group(1)
        _path = _m.group(2)

        _s3 = s3
        if _s3 is None or _s3._t != _bucket:
            from gio import cache_mag
            _s3 = cache_mag.s3(_bucket)

        self._bucket = _bucket
        self._path = _path

        self._f = f
        self._s3 = _s3
        self._s3_inner = s3 is None

        obj_mag.__init__(self)

    def exists(self):
        if not self._path:
            return False
            
        return self._s3.exists(self._path)

    def get(self):
        if not self._path:
            return None
            
        _o = self._s3.get(self._path)
        if _o:
            if self._path.endswith('.shp'):
                for _e in ['.prj', '.shx', '.dbf']:
                    self._s3.get(self._path[:-4] + _e)
        
        return _o
    
    def _list(self, d, fs):
        if str(d).endswith('/'):
            for _f in d.list(False):
                self._list(_f, fs)
        else:
            fs.append(d)

    def list(self, recursive=False):
        if recursive:
            _fs = []
            self._list(self, _fs)
            return _fs
            
        # return [s3_mag('s3://%s/%s' % (self._bucket, _f.key), s3=self._s3) for _f in list(self._s3.bucket.list(self._path))]
        return [s3_mag('s3://%s/%s' % (self._bucket, _f.key), s3=self._s3) for _f in self._s3.list(self._path)]

    def put(self, f, update=True):
        self._s3.put(self._path, f, update=update)

        if self._path.endswith('.shp') and f.endswith('.shp'):
            import os
            for _e in ['.prj', '.shx', '.dbf']:
                _f = f[:-4] + _e
                if os.path.exists(_f):
                    self._s3.put(self._path[:-4] + _e, _f)

    def __str__(self):
        return self._f
        
    def __exit__(self, type, value, traceback):
        if self._s3_inner:
            self._s3.clean()

def get(f):
    if not f:
        return None
        
    _f = f.strip()
    if _f.startswith('s3://'):
        return s3_mag(_f)

    return file_mag(_f)

