'''
File: file_unzip.py
Author: Min Feng
Version: 0.1
Create: 2012-05-30 18:42:22
Description: utility library for compress/uncompress file/folder
'''

_block_size = 1024 * 1024

import logging

def send_to_s3(f, f_out, update=True):
    from . import file_mag
    file_mag.get(f_out).put(f, update)

def uncompress_file(f, d_ot):
    import gzip
    import os

    _fo = d_ot
    if os.path.isdir(d_ot):
        _fo = os.path.join(d_ot, os.path.basename(f)[:-3])
    else:
        # skip if the file is already unzipped
        if os.path.exists(_fo) and os.path.getsize(_fo) > 0:
            return

        _do = os.path.dirname(_fo)
        if _do:
            os.path.exists(_do) or os.makedirs(_do)

    _ft = _fo + '.tmp'

    logging.debug('unzipping %s: %s' % (f, _ft))
    try:
        with gzip.open(f, 'rb') as _f_in:
            with open(_ft, 'wb') as _f_ot:
                while True:
                    _dat = _f_in.read(_block_size)
                    if not _dat:
                        break
                    _f_ot.write(_dat)
                _f_ot.flush()

            import shutil
            shutil.move(_ft, _fo)
    except BaseException as err:
        os.path.exists(_ft) and os.remove(_ft)
        raise err

def uncompress_folder(d_in, d_ot):
    import os, shutil

    # create the folder for output
    os.path.exists(d_ot) or os.makedirs(d_ot)

    for _f in os.listdir(d_in):
        _ff = os.path.join(d_in, _f)

        # process folder
        if os.path.isdir(_ff):
            uncompress_folder(_ff, os.path.join(d_ot, _f))
            continue

        # process file
        if _f.endswith('.gz'):
            uncompress_file(_ff, d_ot)
        else:
            shutil.copy(_ff, d_ot)

def compress_file(f_src, f_dst=None, remove_src=True):
    import gzip
    import os

    _f_dst = f_dst
    if not _f_dst:
        _f_dst = os.path.dirname(f_src)
        if not _f_dst:
            _f_dst = '.'

    if os.path.isdir(_f_dst):
        _f_dst = os.path.join(_f_dst, os.path.basename(f_src) + '.gz')

    with file_unzip() as _zip:
        if f_dst.startswith('s3://'):
            _f_tmp = _zip.generate_file('', '.tmp')
        else:
            _f_tmp = _f_dst + '.tmp'

        # try:
        logging.debug('compress %s to %s' % (f_src, _f_dst))
        with open(f_src, 'rb') as _zip_src:
            (lambda x: (os.path.exists(x) or os.makedirs(x)))(os.path.dirname(_f_tmp))
            with open(_f_tmp, 'wb') as _ft:
                with gzip.GzipFile(_f_dst, 'wb', fileobj=_ft) as _zip_tar:
                    while True:
                        _dat = _zip_src.read(_block_size)
                        if not _dat:
                            break
                        _zip_tar.write(_dat)
                    _zip_tar.flush()

                import time
                time.sleep(0.1)
                _ft.flush()

        # import time
        # time.sleep(1)

        if f_dst.startswith('s3://'):
            send_to_s3(_f_tmp, _f_dst)
        else:
            (lambda x: os.path.exists(x) or os.makedirs(x))(os.path.dirname(_f_dst))

            import shutil
            shutil.move(_f_tmp, _f_dst)

        if remove_src:
            os.remove(f_src)

        # except BaseException, err:
        #     import os
        #     os.path.exists(_f_tmp) and os.remove(_f_tmp)

        #     raise err

def check_prefix(f, exts):
    if not f:
        return False

    if exts == None:
        return True

    for _ext in exts:
        if f.endswith(_ext):
            return True

    return False

def copy_file(f_inp, f_out, compress_exts=None, exclude_exts=None, include_exts=None):
    if exclude_exts and check_prefix(f_inp, exclude_exts):
        return

    if include_exts and not check_prefix(f_inp, include_exts):
        return

    if check_prefix(f_inp, compress_exts):
        _f_ot = f_out + '.gz'
        logging.debug('zipping %s to %s' %(f_inp, _f_ot))

        return compress_file(f_inp, _f_ot)

    logging.debug('copying %s to %s' %(f_inp, f_out))
    if f_out.startswith('s3://'):
        return send_to_s3(f_inp, f_out)

    import os
    import shutil

    _d_out = os.path.dirname(f_out)
    os.path.exists(_d_out) or os.makedirs(_d_out)

    shutil.copy(f_inp, f_out)

def compress_folder(fd_in, fd_ot, compress_exts=None, exclude_exts=None, include_exts=None):
    '''compress files in the folder to the target folder'''
    import shutil
    import os

    if not fd_ot:
        fd_ot = '.'

    logging.debug('compress results from %s to %s' % (fd_in, fd_ot))

    if not os.path.exists(fd_in):
        logging.info('the input folder does not exist %s' % fd_in)
        return
    
    for _file in os.listdir(fd_in):
        _ff = os.path.join(fd_in, _file)

        # process folder
        if os.path.isdir(_ff):
            compress_folder(_ff, os.path.join(fd_ot, os.path.basename(_ff)), compress_exts)
            continue

        # process file
        _f_in = _ff
        _f_ot = os.path.join(fd_ot, _file)

        copy_file(_f_in, _f_ot, compress_exts, exclude_exts, include_exts)

def generate_random_string(length):
    import string
    import random
    
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_id(fd_out, prefix='', subfix=''):
    import os

    _id = '%s%s%s' % (prefix, generate_random_string(10), subfix)
    if fd_out and os.path.exists(os.path.join(fd_out, _id)):
        return generate_id(fd_out, prefix, subfix)

    return _id

def generate_file(fd_out, prefix='', subfix=''):
    if not fd_out:
        raise Exception('invalid path parameter')

    import os
    return os.path.join(fd_out, generate_id(fd_out, prefix, subfix))

def _file_name():
    import sys
    import os

    _f = os.path.basename(os.path.abspath(sys.argv[0]))

    if _f:
        if _f.endswith('.py'):
            return _f[:-3]
        return _f

    raise Exception('failed to detect file name')

def default_tmp_root(fd_out):
    import os, sys

    # use 'tmp' folder at the root of the code when no folder specified
    if fd_out:
        return fd_out

    from . import config

    _d_tmp = config.get('conf', 'temp', os.environ.get('G_TMP', os.path.join(sys.path[0], 'tmp')))

    # if config.cfg.has_option('conf', 'temp'):
    #     _d_tmp = config.
    #     return os.path.join(config.cfg.get('conf', 'temp'), _file_name())

    # if 'G_TMP' in os.environ:
    #     return os.path.join(os.environ['G_TMP'], _file_name())

    if not _d_tmp:
        raise Exception('failed to find temp path')

    return _d_tmp

def default_dir(fd_out):
    import os
    from . import config

    _d_tmp = os.path.join(default_tmp_root(fd_out), _file_name())

    if config.getboolean('conf', 'use_process_temp', False):
        import os
        _d_tmp = os.path.join(_d_tmp, 'p%d' % os.getpid())
        logging.debug('use process temp: %s' % _d_tmp)

    return _d_tmp

def clean(fd_out, remove_root=True):
    '''force to clean the folder'''
    from . import config

    if config.getboolean('conf', 'keep_temp', False):
        logging.warning('keep temp at %s' % fd_out)
        return

    try:
        import shutil, os

        logging.debug('clean folder: %s (%s)' % (fd_out, remove_root))
        if remove_root:
            shutil.rmtree(fd_out, True)
            return

        for _root, _dirs, _files in os.walk(fd_out):
            for _file in _files:
                try:
                    os.remove(os.path.join(_root, _file))
                except Exception:
                    # ignore the errors
                    pass
            for _dir in _dirs:
                shutil.rmtree(os.path.join(_root, _dir), True)

    except Exception:
        pass

class file_unzip:
    def __init__(self, fd_out='', exclusive=True, keep=False):
        import os

        _fd_out = default_dir(fd_out)

        self.pfolder = _fd_out
        self.existed = os.path.exists(_fd_out)

        _fd_out = generate_file(_fd_out)
        os.makedirs(_fd_out)

        self.fd_out = _fd_out
        self.files = []
        self.exclusive = exclusive

        from . import config
        self._keep = keep | config.getboolean('conf', 'keep_temp', False)

        # logging.debug('temp: %s' % self.fd_out)
        # if self._keep:
        #     print('temp:', self.fd_out)

    # support with statement
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return self.clean()

    def generate_file(self, prefix='', subfix=''):
        return generate_file(self.fd_out, prefix, subfix)

    def _estimate_output(self, f, reuse):
        import os
        _f_out = os.path.join(self.fd_out, os.path.basename(f)[:-3])

        if not os.path.exists(_f_out) or reuse:
            return _f_out

        for i in range(10000000):
            _d_out = os.path.join(self.fd_out, 'a%07d' % i)
            if os.path.exists(_d_out):
                continue
            return os.path.join(_d_out, os.path.basename(f)[:-3])

        raise Exception('failed to estimate output file name')

    def unzip(self, f, f_out=None, reuse=False):
        import sys, logging

        if f.lower()[-3:] != '.gz':
            return f

        logging.debug('> unzip ' + f)
        sys.stdout.flush()

        _f_out = f_out
        if not _f_out:
            _f_out = self._estimate_output(f, reuse)

        uncompress_file(f, _f_out)

        if not f_out and (_f_out not in self.files):
            self.files.append(_f_out)

        return _f_out

    def _clean(self):
        from . import config
        if config.getboolean('conf', 'keep_temp', False):
            logging.warning('keep temp at %s' % self.fd_out)
            return

        import shutil, os

        if self.exclusive:
            # shutil.rmtree(self.fd_out if self.existed else self.pfolder, True)
            # forbidden the code for removing the parent dir because it may cause
            #  potential issue for multiple processing, Min, 13/03/03
            shutil.rmtree(self.fd_out, True)
            self.files = []
            return

        for _f in self.files:
            os.remove(_f)
        self.files = []
        return

    def clean(self):
        if self._keep:
            logging.warning('keep temp files %s' % self.fd_out)
        else:
            self._clean()

    def copy(self, fd_in, fd_ot, compress_exts=[], exclude_exts=None, include_exts=None):
        import os

        if not fd_in.startswith('s3://') and os.path.isfile(fd_in):
            return copy_file(fd_in, fd_ot, compress_exts, exclude_exts, include_exts)

        return compress_folder(fd_in, fd_ot, compress_exts=compress_exts, \
            exclude_exts=exclude_exts, include_exts=include_exts)

    def save(self, o, f_out):
        import os

        if o is None:
            logging.warning('skip saving none object to %s' % f_out)
            return

        _d_tmp = self.generate_file()
        _f_tmp = os.path.join(_d_tmp, os.path.basename(f_out))

        os.makedirs(_d_tmp)
        
        _b = o
        if isinstance(_b, str):
            _b = o.encode('utf-8')
            
        if f_out.endswith('.gz'):
            from gio import config
            _auto = config.getboolean('conf', 'auto_gzip_file', True)
            if _auto:
                import gzip
                _b = gzip.compress(_b)
            
        if isinstance(_b, bytes):
            with open(_f_tmp, 'wb') as _fo:
                _fo.write(_b)
        else:
            # from . import geo_raster as ge
            # if isinstance(o, ge.geo_band_cache):
            
            o.save(_f_tmp)

        if os.path.exists(_f_tmp) == False:
            raise Exception('failed to save the object')

        _d_out = os.path.dirname(f_out)
        if not _d_out:
            _d_out = '.'

        self.copy(_d_tmp, _d_out)

zip = file_unzip

def save(o, f_out):
    with zip() as _zip:
        return _zip.save(o, f_out)

def copy(self, fd_in, fd_ot, exclude_exts=None, include_exts=None):
    with zip() as _zip:
        return _zip.copy(fd_in, fd_ot, exclude_exts, include_exts)
