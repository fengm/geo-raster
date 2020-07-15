'''
File: environ_mag.py
Author: Min Feng
Version: 0.1
Create: 2016-09-01 13:56:39
Description: provide functions to help commands to setup the environments
'''
def bool_type(v):
    return v.lower() in ("yes", "true", "t", "1")

def usage(multi_task=False):
    import argparse

    _p = argparse.ArgumentParser()
    _p.register('type', 'bool', bool_type)

    _p.add_argument('--logging', dest='logging')
    _p.add_argument('--config', dest='config', nargs='+')
    _p.add_argument('--env', dest='env', nargs='+', action='append')
    _p.add_argument('--debug', dest='debug', action='store_true')
    _p.add_argument('--no-clean', dest='no_clean', action='store_true', help='deprecated')
    _p.add_argument('--clean', dest='clean', type='bool', default=False)
    _p.add_argument('--temp', dest='temp')
    _p.add_argument('--show-progress', dest='show_progress', action='store_true', default=False)

    if multi_task:
        from gio import multi_task
        multi_task.add_task_opts(_p)

    return _p

def init_path():
    import os, sys

    _dirs = ['lib', 'libs']
    _d_ins = [os.path.join(sys.path[0], _d) for _d in _dirs if \
            os.path.exists(os.path.join(sys.path[0], _d))]
    sys.path = [sys.path[0]] + _d_ins + sys.path[1:]

def set_config_items(opts):
    from gio import config

    if not config.cfg.has_section('conf'):
        config.cfg.add_section('conf')

    for _k, _v in list(opts.__dict__.items()):
        if _v is not None:
            config.set('conf', _k, str(_v).replace('%s', '{}'))

def config(p, enable_multi_processing=True):
    _opts = p.parse_args()

    from gio import config
    config.load(_opts.config)

    set_config_items(_opts)
    _parse_env(_opts)

    from gio import logging_util
    logging_util.init(_opts.logging, enable_multi_processing)

    from gio import file_unzip as fz
    # if config.getboolean('conf', 'no_clean', False) == False:
    if config.getboolean('conf', 'clean', False) == True:
        import logging
        logging.info('clean the temporary folder')
        
        fz.clean(fz.default_dir(_opts.temp))

    return _opts
    
def _opts_to_str(opts):
    _vs = []

    for _opts in opts:
        for _k, _v in list({key: value for key, value in list(_opts.__dict__.items()) if not key.startswith("__")}.items()):
            _vs.append('%s=%s' % (_k, _v))
    
    return '; '.join(_vs)

def _parse_env(opts, log=False):
    from gio import config
    import logging
    import re
    
    if not opts.env or len(opts.env) <= 0:
        return
    
    _env = None
    for _e in opts.env:
        if _env is None:
            _env = _e
        else:
            _env.extend(_e)
    
    if not _env:
        return
    
    for _e in _env:
        _es = re.split('\s*\=\s*', _e.strip())
        if len(_es) != 2:
            raise Exception('failed to parse environment variable (%s)' % _e)

        _ns = re.split('[\/\.]', _es[0])
        if len(_ns) > 2:
            raise Exception('failed to parse environment name (%s)' % _es[0])
            
        if len(_ns) == 1:
            _n0 = 'conf'
            _n1 = _ns[0]
        else:
            _n0 = _ns[0]
            _n1 = _ns[1]
        
        if log:
            logging.info('env %s.%s=%s' % (_n0, _n1, _es[1]))
        else:
            config.set(_n0, _n1, _es[1])
            
def run(func, opts):
    import logging
    from . import config
    import os
    from . import file_unzip
    import sys
    from . import logging_util

    logging_util.info(('CMD (%s): ' % os.getcwd()) + ' '.join(['"%s"' % x if ' ' in x else x for x in sys.argv]))
    _parse_env(opts[0], log=True)
    
    os.environ['PATH'] = '.' + os.pathsep + sys.argv[0] + os.pathsep + os.environ['PATH']
    with file_unzip.file_unzip() as _zip:
        _tmp = _zip.generate_file()
        config.set('conf', 'temp', _tmp)

        _cache = config.get('conf', 'cache', None)
        if not _cache:
            config.set('conf', 'cache', os.path.join(_tmp, 'cache'))

        if config.getint('conf', 'task_type') is not None:
            from . import multi_task
            multi_task.init(opts[0])
            
        logging_util.info('options: ' + _opts_to_str(opts))

        if config.getboolean('conf', 'debug', True):
            return func(*opts)
        else:
            try:
                return func(*opts)
            except KeyboardInterrupt:
                print('\n\n* User stopped the program')
            except Exception as err:
                import traceback

                logging_util.error(traceback.format_exc())
                logging_util.error(str(err))

        if os.path.exists(_tmp):
            try:
                import shutil
                shutil.rmtree(_tmp, True)
            except Exception as err:
                pass

    import sys
    sys.exit(1)

if __name__ == '__main__':
    init_path()
    _p = usage()
    _opts = config(_p)
