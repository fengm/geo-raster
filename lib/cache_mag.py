'''
File: cache_mag.py
Author: Min Feng
Version: 0.1
Create: 2016-05-11 15:25:43
Description: manage Landsat cache files
'''

import logging
from . import config

class file_obj():

    def __init__(self, f):
        import os

        self._f = f
        self._t = os.path.getatime(f)
        self._z = os.path.getsize(f)

    def __eq__(self, f):
        return self._t == f._t

_w_lock = {}
_w_nums = {}

def _get_cache_dir(d=None):
    if d:
        return d

    _d_tmp = config.get('conf', 'cache')
    if _d_tmp:
        return _d_tmp

    from . import file_unzip
    import os

    return os.path.join(file_unzip.default_dir(None), 'cache')

class cache_mag():
    """manage Landsat cache files"""

    def __init__(self, tag, cache=None, max_file=-1, max_size=-1):
        self._t = tag
        self._d = _get_cache_dir(cache)

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
            _p = _get_cache_dir()
            if not _p:
                if _zip is None:
                    raise Exception('need to provide zip obj when cache is disabled')

                logging.info('disabled caching S3 files')
                _p = _zip.generate_file()

        self._zip = _zip
        self._zip_inner = fzip is None

        self._path = _p
        self._c = cache_mag(bucket, _p)

        self.bucket = self._t

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.clean()

    def _get_s3_client(self):
        import boto3
        return boto3.client('s3')

    def clean(self):
        if (not self._enable_cache) and (self._path):
            import shutil
            shutil.rmtree(self._path, True)

        if self._zip_inner and self._zip:
            self._zip.clean()

    def _list_by_resource(self, k, recursive=True, limit=-1):
        import boto3

        _ps = {'Prefix': k}
        if not recursive:
            _ps['Delimiter'] = '/'
            
        _ss = boto3.resource('s3').Bucket(self._t)
        if limit >= 0:
            return list(_ss.objects.filter(**_ps).limit(limit))

        _ls = list(_ss.objects.filter(**_ps))
        return _ls

    def _list_by_client(self, k, recursive=True, limit=-1):
        _paginator = self._get_s3_client().get_paginator("list_objects_v2")

        _ps = {'Bucket': self._t, 'Prefix': k}
        
        if not recursive:
            _ps['Delimiter'] = '/'

        if config.getboolean('aws', 's3_requester_pay', True):
            _ps['RequestPayer'] = 'requester'

        if limit >= 0:
            _ps['MaxKeys'] = limit

        _ts = []
        for _page in _paginator.paginate(**_ps):
            # list files
            for _k in _page.get('Contents', []):
                if k.endswith('/') and _k.get('Key') == k:
                    # skip folders
                    continue
                _ts.append(_k)
            
            # include subfolders
            if not recursive:
                for _k in _page.get('CommonPrefixes', []):
                    _ts.append(_k)

        return _ts

    def list(self, k, recursive=True, limit=-1):
        if config.getboolean('aws', 's3_requester_pay', True):
            return self._list_by_client(k, recursive, limit)

        return [{'Key': _s.key} for _s in self._list_by_resource(k, recursive, limit)]

    def exists(self, k):
        if not k:
            return False

        _os = self.list(k, limit=1)
        return len(_os) > 0

    def remove(self, key):
        import boto3

        _ss = boto3.resource('s3')
        _bk = _ss.Bucket(self._t)

        _nu = 0
        for _o in _bk.objects.filter(Prefix=key):
            _ss.Object(self._t, _o.key).delete()
            _nu += 1

        return _nu

    # def remove(self, key):
    #     from . import config

    #     _ps = {'Bucket': self._t, 'Key': key}
    #     if config.getboolean('aws', 's3_requester_pay', True):
    #         _ps['RequestPayer'] = 'requester'

    #     return self._get_s3_client().delete_object(**_ps)

    def get(self, k, lock=None):
        if k is None:
            return None

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
        # if config.getboolean('conf', 's3_get_with_cli', False):
        #     return self._get_cli(k, lock)

        return self._get_boto(k, lock)

    # download file using boto3 function
    def _get_boto(self, k, lock=None):
        if k is None:
            return None

        _key = k if isinstance(k, str) or isinstance(k, str) else k.key
        _f = self._c.path(_key)

        if self._c.cached(_key):
            logging.debug('found cached file %s' % _f)
            return _f

        import os
        import shutil
        from . import file_unzip

        for _i in range(3):
            _t = file_unzip.generate_file(os.path.dirname(_f), '', '.bak')

            try:
                (lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_t))
                
                # write an empty file to prevent other process to use the same file name
                with open(_t, 'w') as _fo:
                    _fo.write('')

                _ps = {'Bucket': self._t, 'Key': k}
                if config.getboolean('aws', 's3_requester_pay', True):
                    _ps['RequestPayer'] = 'requester'

                try:
                    _rs = self._get_s3_client().get_object(**_ps)
                except Exception as _err:
                    # import traceback
                    # logging.debug(traceback.format_exc())
                    logging.debug(str(_err))
                    # print('\n\n* Error:', _err)

                    # import time
                    # time.sleep(1)

                    logging.debug('failed to load key s3://%s/%s' % (self._t, k))
                    # continue
                    return None

                _bd = _rs['Body']

                _sz = 0.0
                with open(_t, 'wb') as _fo:
                    for _bs in _bd.iter_chunks():
                        _fo.write(_bs)
                        _sz += float(len(_bs))
                        del _bs

                if not os.path.exists(_t) or _sz < _rs['ContentLength']:
                    logging.warning('received partial file from S3 (%s, %s)' % (_sz, _rs['ContentLength']))
                    os.remove(_t)
                    continue

                if lock is None:
                    if os.path.exists(_f) == False:
                        shutil.move(_t, _f)
                else:
                    with lock:
                        if os.path.exists(_f) == False:
                            shutil.move(_t, _f)

                return _f
                
            except Exception:
                pass
            finally:
                if os.path.exists(_t):
                    os.remove(_t)

        raise Exception('failed to load S3 file s3://%s/%s' % (self._t, _key))

    # download file usign awscli command to test the issue that likely related to boto3
    def _get_cli(self, k, lock=None):
        if k is None:
            return None

        _key = k if isinstance(k, str) or isinstance(k, str) else k.key
        _f = self._c.path(_key)

        if self._c.cached(_key):
            # logging.debug('found cached file %s' % _f)
            return _f

        import os
        try:
            (lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f))
        except Exception:
            pass

        import shutil
        from . import file_unzip

        for _i in range(1):
            _t = file_unzip.generate_file(os.path.dirname(_f), '', '.bak')

            try:
                # write an empty file to prevent other process to use the same file name
                with open(_t, 'w') as _fo:
                    _fo.write('')

                _cmd = 'aws s3 cp s3://%s/%s %s' % (self._t, k, _t)
                if config.getboolean('aws', 's3_requester_pay', True):
                    _cmd = _cmd + ' --request-pay requester'

                from . import run_commands as run
                run.run(_cmd)

                if os.path.getsize(_t) <= 1:
                    logging.warning('failed to receive file from S3 (%s://%s)' % (self._t, k))
                    os.remove(_t)
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

        raise Exception('failed to load S3 file s3://%s/%s' % (self._t, _key))

    def put(self, k, f, update=True, lock=None):
        if (not update) and self.exists(k):
            logging.info('skip existing file %s: %s' % (self._t, k))
            return

        logging.info('upload file %s: %s' % (self._t, k))
        with open(f, 'rb') as _fi:
            _ps = {'Bucket': self._t, 'Key': k, 'Body': _fi}
            if config.getboolean('aws', 's3_requester_pay', True):
                _ps['RequestPayer'] = 'requester'

            _rs = self._get_s3_client().put_object(**_ps)

def parse_s3(f):
    import re

    _m = re.match('s3://([^/]+)/(.+)', f)
    if _m is None:
        raise Exception('failed to parse S3 file %s' % f)

    _bucket = _m.group(1)
    _path = _m.group(2)

    return _bucket, _path
