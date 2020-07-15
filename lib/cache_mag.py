'''
File: cache_mag.py
Author: Min Feng
Version: 0.1
Create: 2016-05-11 15:25:43
Description: manage Landsat cache files
'''

import logging

class file_obj():

    def __init__(self, f):
        import os

        self._f = f
        self._t = os.path.getatime(f)
        self._z = os.path.getsize(f)

    def __cmp__(self, f):
        return cmp(self._t, f._t)

_w_lock = {}
_w_nums = {}

class cache_mag():
    """manage Landsat cache files"""

    def __init__(self, tag, cache=None, max_file=-1, max_size=-1):
        from . import config

        self._t = tag
        
        if cache:
            self._d = cache
        else:
            self._d = config.get('conf', 'cache')

        if not self._d:
            raise Exception('no cache folder specified')

        self._max_file = config.getint('conf', 'max_cached_file', max_file)
        self._max_size = config.getfloat('conf', 'max_cached_size', max_size)

        # self._n = 0

        global _w_nums
        if self._t not in _w_nums:
            _w_nums[self._t] = 0.0

        global _w_lock
        if self._t not in _w_lock:
            if config.getboolean('conf', 'enable_cache_lock', True):
                from . import multi_task
                _w_lock[self._t] = multi_task.create_lock()

    def cached(self, key):
        _f = self.path(key)
        import os
        return os.path.exists(_f) and os.path.getsize(_f) > 0

    def _format_str(self, t):
        import re
        _k = list(re.sub('[^\w\d_]', '_', t))

        for i in range(len(_k)):
            if t[i] in ['\\', '/', '.', '-']:
                _k[i] = t[i]

        return ''.join(_k)

    def path(self, key):
        import os

        _p = self._format_str(key)
        if _p and _p[0] in ['/', '\\']:
            # remove the root path if it exists
            _p = _p[1:]

        _f = os.path.join(self._d, self._t, _p)

        import os
        if os.path.exists(_f):
            os.utime(_f, None)

        return _f

    def get(self, key):
        if not self.cached(key):
            return None

        return self.path(key)

    def _put(self, inp, f):
        import os
        _f = f

        if os.path.exists(_f):
            return _f

        if self._max_file > 0 or self._max_size > 0:
            global _w_nums
            _w_nums[self._t] += 1

            if _w_nums[self._t] > (self._max_file / 10 if self._max_file > 0 else 1000):
                self._clean()
                _w_nums[self._t] = 0

        try:
            (lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))
        except Exception:
            pass

        import random
        _f_out = _f + str(random.randint(0, 1000)) + '.bak'

        import shutil
        shutil.copy(inp, _f_out)

        if os.path.exists(_f) == False:
            shutil.move(_f_out, _f)
        else:
            os.remove(_f_out)

        return _f

    def put(self, key, inp=None, replace=False):
        import os

        _f = self.path(key)
        _inp = inp if inp else key

        if self.cached(key):
            if replace:
                logging.info('clear cached %s' % key)
                try:
                    os.remove(_f)
                except Exception:
                    pass
            else:
                logging.info('loading cached %s' % key)
                return _f

        global _w_lock
        if self._t in _w_lock:
            with _w_lock[self._t]:
                self._put(_inp, _f)
        else:
            self._put(_inp, _f)

        return _f

    def _clean_file(self, f):
        try:
            import os
            os.remove(f._f)
            logging.info('clean cached file %s' % f._f)
        except Exception as err:
            import traceback

            logging.error(traceback.format_exc())
            logging.error(str(err))

            print('\n\n* Error:', err)

    def _clean(self):
        import os

        logging.info('clean cache')

        # self._n = 0
        _w_nums[self._t] == 0

        _fs = []
        _sz = 0.0
        for _root, _dirs, _files in os.walk(self._d):
            for _file in _files:
                _ff = os.path.join(_root, _file)
                if _file.endswith('.bak'):
                    import time
                    # remove bak files that has not been used for 24 hours
                    if (time.time() - os.path.getatime(_ff)) > 60 * 60 * 24:
                        logging.warning('remove bak file %s' % _ff)
                        os.remove(_ff)
                    continue

                _fs.append(file_obj(_ff))
                _sz += os.path.getsize(_ff)

        _fs = sorted(_fs)

        logging.info('checking cache %s, %s (%s, %s)' % (len(_fs), _sz, self._max_file, self._max_size))

        _fd1 = []
        if self._max_file > 0 and len(_fs) > self._max_file:
            _fd = _fs[:self._max_file-len(_fs)]

        _fd2 = []
        if self._max_size > 0:
            # convert from GB
            self._max_size *= (1024 * 1024 * 1024)

        if self._max_size > 0 and _sz > self._max_size:
            _zz = _sz
            for _f in _fs:
                _fd2.append(_f)
                _zz -= _f._z

                if _zz <= self._max_size:
                    break

        _fd = _fd1 if len(_fd1) > len(_fd2) else _fd2
        logging.info('identified cached files to clean %s %s %s' % (len(_fd), len(_fd1), len(_fd2)))

        for _f in _fd:
            self._clean_file(_f)

_get_cache_que = None

class s3():
    """manage Landsat cache files"""

    def __init__(self, bucket, fzip=None):
        from gio import config

        self._t = bucket
        _zip = fzip

        self._enable_cache = config.getboolean('conf', 'enable_s3_cache', True)
        if not self._enable_cache:
            logging.info('disabled caching S3 files')
            if _zip is None:
                from gio import file_unzip
                _zip = file_unzip.file_unzip()
                
            _p = _zip.generate_file()
        else:
            _p = config.get('conf', 'cache')
            if not _p:
                if _zip is None:
                    raise Exception('need to provide zip obj when cache is disabled')
    
                logging.info('disabled caching S3 files')
                _p = _zip.generate_file()

        self._zip = _zip
        self._zip_inner = fzip is None
        
        self._path = _p
        self._c = cache_mag(bucket, _p)

        import boto3
        self._s3 = boto3.resource('s3')
        self.bucket = self._s3.Bucket(self._t)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.clean()
    
    def clean(self):
        if (not self._enable_cache) and (self._path):
            import shutil
            shutil.rmtree(self._path, True)
            
        if self._zip_inner and self._zip:
            self._zip.clean()

    def list(self, k, limit=-1):
        if limit >= 0:
            return list(self.bucket.objects.filter(Prefix=k).limit(limit))
            
        _ls = list(self.bucket.objects.filter(Prefix=k))
        return _ls

    def exists(self, k):
        if not k:
            return False
            
        if k.endswith('/'):
            _os = self.list(k, limit=1)
            return len(_os) > 0
            
        _k = self.get_key(k)
        if _k is None:
            return False
            
        return True

    def get(self, k, lock=None):
        if k is None:
            return None

        from gio import config
        _enable_lock = config.getboolean('conf', 'enable_cache_lock', True)

        if _enable_lock:
            _num = config.getint('conf', 'max_cache_rec_num', 2)
        else:
            _num = 0

        if _num <= 0:
            return self._get(k, lock)

        global _get_cache_que
        if _get_cache_que is None:
            import multiprocessing
            _get_cache_que = multiprocessing.Semaphore(value=_num)

        with _get_cache_que:
            return self._get(k, lock)

    def _get(self, k, lock=None):
        if k is None:
            return None

        _key = k if isinstance(k, str) or isinstance(k, str) else k.key
        _f = self._c.path(_key)

        if self._c.cached(_key):
            logging.debug('found cached file %s' % _f)
            return _f

        import os
        try:
            (lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))
        except Exception:
            pass

        import shutil
        from . import file_unzip

        for _i in range(3):
            _t = file_unzip.generate_file(os.path.dirname(_f), '', '.bak')

            try:
                # write an empty file to prevent other process to use the same file name
                with open(_t, 'w') as _fo:
                    _fo.write('')

                _kkk = self.get_key(k)
                if _kkk is None:
                    logging.warning('no key was found: %s' % k)
                    return None
                    
                with open(_t, 'wb') as _fo:
                    _kkk.download_fileobj(_fo)

                if not os.path.exists(_t) or os.path.getsize(_t) < _kkk.content_length:
                    logging.warning('received partial file from S3 (%s, %s)' % (os.path.getsize(_f), _kkk.size))
                    continue

                if lock is None:
                    if os.path.exists(_f) == False:
                        shutil.move(_t, _f)
                else:
                    with lock:
                        if os.path.exists(_f) == False:
                            shutil.move(_t, _f)

                return _f

            finally:
                if os.path.exists(_t):
                    os.remove(_t)

        raise Exception('failed to load S3 file %s' % _key)

    def get_key(self, k):
        if not k:
            return None
            
        _k = self._s3.Object(self._t, k) if isinstance(k, str) or isinstance(k, unicode) else k
        
        if _k is None:
            return None
        
        from botocore.exceptions import ClientError        
        try:
            _k.content_length
        except ClientError:
            return None

        return _k

    # def new_key(self, k):
    #     _kk = self.bucket.new_key(k) if isinstance(k, str) or isinstance(k, unicode) else k
    #     return _kk

    def put(self, k, f, update=True, lock=None):
        _kk = self.get_key(k)
        if _kk is not None:
            if update == False:
                logging.info('skip existing file %s: %s' % (_kk.bucket, _kk.name))
                return

        _b, _p = self._t, k
        logging.info('upload file %s: %s' % (_b, _p))

        if lock is None:
            self.bucket.upload_file(f, _p)
        else:
            with lock:
                self.bucket.upload_file(f, _p)

def parse_s3(f):
    import re

    _m = re.match('s3://([^/]+)/(.+)', f)
    if _m is None:
        raise Exception('failed to parse S3 file %s' % f)

    _bucket = _m.group(1)
    _path = _m.group(2)

    return _bucket, _path
