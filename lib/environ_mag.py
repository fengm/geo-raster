'''
File: environ_mag.py
Author: Min Feng
Version: 0.1
Create: 2016-09-01 13:56:39
Description: provide functions to help commands to setup the environments
'''

def usage(multi_task=False):
    import argparse

    _p = argparse.ArgumentParser()
    _p.add_argument('--logging', dest='logging')
    _p.add_argument('--config', dest='config', nargs='+')
    _p.add_argument('--debug', dest='debug', action='store_true')
    _p.add_argument('--no-clean', dest='no_clean', action='store_true')
    _p.add_argument('--temp', dest='temp')

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

def config(p, enable_multi_processing=True):
    _opts = p.parse_args()

    from gio import config
    config.load(_opts.config)

    if not config.cfg.has_section('conf'):
        config.cfg.add_section('conf')

    # if not _opts.logging and 'output' in _opts:
    #     _opts.logging = os.path.join(_opts.output, 'log.txt')

    for _k, _v in _opts.__dict__.items():
        if _v is not None:
            config.cfg.set('conf', _k, str(_v))

    from gio import logging_util
    logging_util.init(_opts.logging, enable_multi_processing)

    from gio import file_unzip as fz
    if config.getboolean('conf', 'no_clean', False) == False:
        fz.clean(fz.default_dir(_opts.temp))

    return _opts

def run(func, opts):
    import logging
    import config

    if config.getboolean('conf', 'debug', True):
        return func(*opts)
    else:
        try:
            return func(*opts)
        except KeyboardInterrupt:
            print '\n\n* User stopped the program'
        except Exception, err:
            import traceback

            logging.error(traceback.format_exc())
            logging.error(str(err))

            print '\n\n* Error:', err

            from gio import logging_util
            if logging_util.cloud_enabled():
                _log = logging_util.cloud()
                _log.error(traceback.format_exc())
                _log.error(str(err))

        import sys
        sys.exit(1)

if __name__ == '__main__':
    init_path()
    _p = usage()
    _opts = config(_p)

