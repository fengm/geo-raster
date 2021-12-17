'''
File: logging_util.py
Author: Min Feng
Version: 0.1
Create: 2013-06-14 15:11:29
Description: initilize the logging module
'''

import logging

class sync_file_log_handler(logging.FileHandler):

    def __init__(self, filename, mode='a', encoding=None):
        import multiprocessing
        self.p_lock = multiprocessing.Lock()
        import threading
        self.t_lock = threading.Lock()

        import os
        _d_log = os.path.dirname(os.path.abspath(filename))
        os.path.exists(_d_log) or os.makedirs(_d_log)

        logging.FileHandler.__init__(self, filename, mode=mode, encoding=encoding)

    def emit(self, record):
        with self.p_lock:
            with self.t_lock:
                logging.FileHandler.emit(self, record)

def find_log(f=None):
    import sys, os, re

    _f = f
    if not _f:
        _f = os.path.basename(sys.argv[0])
        _m = re.match('(.+)\.[^\.]+$', _f)
        if _m:
            _f = _m.group(1)

        # import datetime
        # _f += '_%s.log' % datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        if 'G_LOG' in os.environ:
            _f = os.path.join(os.environ['G_LOG'], _f + '.log')
        else:
            _f = os.path.join(sys.path[0], 'log', _f + '.log')

    return _f

log_file = None

def _env_int_val(tag, val):
    import os
    
    if tag in os.environ:
        return int(os.environ[tag])
    return val

def init(f=None, enable_multi_processing=False):
    from . import config
    import os

    _log = logging.getLogger()

    _f = find_log(f)
    global log_file
    log_file = _f

    _d_log = os.path.dirname(os.path.abspath(_f))
    try:
        os.path.exists(_d_log) or os.makedirs(_d_log)
    except Exception:
        pass

    _debug = config.getboolean('conf', 'debug') if config.cfg else False
    if _debug:
        print(' - debugging')
        print(' - log file', _f)

    _level_out = config.getint('conf', 'log_out_level', _env_int_val('LOG_OUT_LEVEL', -1))
    _level_std = config.getint('conf', 'log_std_level', _env_int_val('LOG_STD_LEVEL', -1))
    
    _log.setLevel(logging.DEBUG)

    if len(_log.handlers) == 0:
        import sys
        _log.addHandler(logging.StreamHandler(sys.stdout))

    _handler = _log.handlers[0]

    _level = 30 if not _debug else 20
    if _level_std >= 0:
        _level = _level_std

    _handler.setLevel(_level)

    if _debug:
        _handler.setFormatter(logging.Formatter('%(asctime)-15s:%(levelname)s: %(message)s'))
    else:
        _handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

    # print 'logging file', _f
    if enable_multi_processing:
        _handler = sync_file_log_handler(_f)

        _level = 20 if not _debug else 10
        if _level_out >= 0:
            _level = _level_out

        _handler.setLevel(_level)

        if _debug:
            _handler.setFormatter(logging.Formatter('%(process)d:%(asctime)-15s:%(levelname)s: %(message)s'))
        else:
            _handler.setFormatter(logging.Formatter('%(process)d:%(asctime)-15s:%(levelname)s: %(message)s'))
            # _handler.setFormatter(logging.Formatter('%(process)d:%(levelname)s:%(message)s'))

        _log.addHandler(_handler)

    # logging.basicConfig(filename=_f, level=logging.DEBUG, filemode=filemode, format=format)
    if cloud_enabled():
        _log = cloud()

        import watchtower
        _log.addHandler(watchtower.CloudWatchLogHandler())
        _log.setLevel(logging.DEBUG)

def cloud_enabled():
    import os

    if 'CLOUDWATCH_LOG' in os.environ:
        if os.environ['CLOUDWATCH_LOG'] in ['yes', '1']:
            return True

    return False

def cloud(tag='cloud'):
    return logging.getLogger(tag)
    
def info(t):
    logging.info(t)
    
    if cloud_enabled():
        cloud().info(t)

def debug(t):
    logging.debug(t)
    
    if cloud_enabled():
        cloud().debug(t)
        
def warning(t):
    logging.warning(t)
    
    if cloud_enabled():
        cloud().warning(t)
        
def error(t):
    logging.error(t)
    
    if cloud_enabled():
        cloud().error(t)
