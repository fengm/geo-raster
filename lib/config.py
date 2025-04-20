'''
File: config.py
Author: Min Feng
Version: 0.1
Create: 2014-03-18 02:02:29
Description: help locate and read the configuration file
'''
# updated (2017-01-20 02:05:18): updated to support use all config files in a dir or listed in a list file as config inputs

import collections
import logging

cfg = None

def _exist_file(f):
    import os
    return os.path.exists(f) and os.path.isfile(f)

def _detect_sys(f, ext):
    import os
    import sys

    _f = f + (ext if ext.startswith('.') else ('.' + ext))

    _f_cfg = os.path.join(sys.argv[0], _f)
    if _exist_file(_f_cfg):
        return _f_cfg

    _f_cfg = os.path.join(sys.path[0], 'conf', _f)
    if _exist_file(_f_cfg):
        return _f_cfg

    _f_cfg = os.path.join(sys.path[0], 'etc', _f)
    if _exist_file(_f_cfg):
        return _f_cfg

    if 'G_INI' in os.environ and os.environ['G_INI']:
        _f_cfg = os.path.join(os.environ['G_INI'], _f)
        if _exist_file(_f_cfg):
            return _f_cfg

    return None

def _detect_file(f_cfg):
    import os, sys, re

    if f_cfg:
        _f = f_cfg
    else:
        _f = os.path.basename(sys.argv[0])
        _m = re.match(r'(.+)\.[^\.]+$', _f)
        if _m:
            _f = _m.group(1)

    if _exist_file(_f):
        return _f

    _f = _detect_sys(_f, 'conf') or _detect_sys(_f, 'ini')
    return _f

def _load_dir(d):
    import os

    _fs = []
    for _root, _dirs, _files in os.walk(d):
        for _file in _files:
            _ext = os.path.splitext(_file)[-1]
            if _ext in ['.ini', '.conf']:
                _fs.append(os.path.join(_root, _file))

    return _fs

def _load_file(f):
    _fs = []

    with open(f) as _fi:
        _ls = _fi.read().strip().splitlines()
        for _l in _ls:
            _l = _l.strip()
            if _l.startswith('#') or _l.startwith(';'):
                continue

            _fs.append(_l)

    return _fs

def load(f_cfg=None, defaults=None, dict_type=collections.OrderedDict, allow_no_value=False):
    global cfg

    import os
    _fs = []

    for _f in (f_cfg if (isinstance(f_cfg, list) or isinstance(f_cfg, tuple)) else [f_cfg]):
        if not _f:
            _l = _detect_file(None)
            if _l:
                _fs.append(_l)
            continue
        
        _f = _f.strip()
        
        # support S3 config file
        if _f.startswith('s3://'):
            _d_ini = os.environ['G_INI']
            if not _d_ini:
                raise Exception('failed to find the G_INI environ')
                
            _f_out = os.path.abspath(os.path.join(_d_ini, _f[5:]))
            # if not os.path.exists(_f_out):
            # if os.path.exists(_f_out):
            if True:
                # update the config file every time
                os.system('aws s3 cp %s %s' %  (_f, _f_out))
            _f = _f_out

        if os.path.exists(_f):
            if os.path.isdir(_f):
                _fs.extend(_load_dir(_f))
                continue

            if os.path.splitext(_f)[-1] in ['.txt']:
                _fs.extend(_load_file(_f))
                continue
            
        _l = _detect_file(_f)
        if _l:
            _fs.append(_l)

    for _l in _fs:
        logging.info('loading config file: %s' % _l)

    import sys
    _df = {'root': sys.path[0]}

    if len(_fs) > 0:
        _df['config_path'] = os.environ['G_INI']
        _df['config_file'] = os.path.basename(_fs[0])
        _df['ini_path'] = os.path.dirname(_fs[0])

        if len(_fs) > 1:
            logging.warning('config file %s is used for config_path and config_file parameters' % _fs[0])

    defaults != None and _df.update(defaults)

    import configparser
    # cfg = configparser.ConfigParser(_df, dict_type, allow_no_value, interpolation=configparser.ExtendedInterpolation())
    cfg = configparser.ConfigParser(_df, dict_type, allow_no_value)
    len(_fs) and cfg.read(_fs)
    
    logging.debug('loading sys varaibles')
    
    import os
    import re
    from . import config
    
    for _k in os.environ:
        _m = re.match(r'^G_(.+)$', _k)
        if _m:
            logging.debug('add sys var %s' % _m.group(1).upper())
            _set('sys', _m.group(1).upper(), os.environ[_k])
            
def _get_cfg():
    global cfg
    
    if cfg is None:
        load()
        
    return cfg

def get_attr(section, name):
    return _get_cfg().get(section, name)

def get_at(section, name):
    return get_attr(section, name)

def items(section):
    _cfg = _get_cfg()

    if section not in _cfg.sections():
        return

    _ns = _cfg.defaults()
    for _n, _v in _cfg.items(section):
        if _n in _ns:
            continue

        yield _n, _v

def set(section, name, val):
    return _set(section, name, val)
    
def _set(section, name, val):
    _cfg = _get_cfg()

    # set the value to None is to delete the option
    if val is None:
        if _cfg.has_option(section, name):
            _cfg.remove_option(section, name)
        return

    if _cfg.has_section(section) == False:
        _cfg.add_section(section)

    logging.debug('setting config %s=%s' % (section + '.' + name, val))
    _val = str(val) if val is not None else None
    _cfg.set(section, name, _val)
    
def _get_sys_var(section, name, val):
    _cfg = _get_cfg()
    if section != 'conf':
        return val
        
    _n = name.upper()
    if _cfg.has_option('sys', _n):
        _v = _cfg.get('sys', _n)
        return _v
            
    return val

def get(section, name, val=None):
    """get config param

    :section: section
    :name: option name
    :val: default value
    :returns: config value

    """
    _cfg = _get_cfg()

    if not _cfg.has_option(section, name):
        _v = _get_sys_var(section, name, val)
        
        if _v is None:
            return val
            
        return _v
        
    return _cfg.get(section, name)

def getint(section, name, val=None):
    """get config param

    :section: section
    :name: option name
    :val: default value
    :returns: config value

    """
    _cfg = _get_cfg()

    if not _cfg.has_option(section, name):
        _v = _get_sys_var(section, name, val)
        
        if _v is None:
            return val
            
        return int(_v)

    return _cfg.getint(section, name)

def getfloat(section, name, val=None):
    """get config param

    :section: section
    :name: option name
    :val: default value
    :returns: config value

    """
    _cfg = _get_cfg()

    if not _cfg.has_option(section, name):
        _v = _get_sys_var(section, name, val)
        
        if _v is None:
            return val
            
        return float(_v)

    return _cfg.getfloat(section, name)

def getboolean(section, name, val=None):
    """get config param

    :section: section
    :name: option name
    :val: default value
    :returns: config value

    """
    _cfg = _get_cfg()

    if not _cfg.has_option(section, name):
        _v = _get_sys_var(section, name, val)
        
        if _v is None:
            return val
            
        return str(_v).lower() in ('true', '1', 'yes', 'y')

    return _cfg.getboolean(section, name)

def getjson(section, name, val=None):
    """get config param

    :section: section
    :name: option name
    :val: default value
    :returns: config value

    """
    _cfg = _get_cfg()

    _v = None
    if not _cfg.has_option(section, name):
        _v = _get_sys_var(section, name, val)
    else:
        _v = _cfg.get(section, name)

    if _v is None:
        return val

    import json
    return json.loads(_v.replace("'", '"'))

def has_option(section, name):
    """get config param

    :section: section
    :name: option name
    :val: default value
    :returns: config value

    """
    return _get_cfg().has_option(section, name)

def main(opts):
    from gio import config
    print('#', config.get('conf', 'test1'))
    print('*', config.get('conf', 'test2'))
    print('#', config.get('conf', 'test3'))
    print('*', config.get('conf', 'test4'))

def usage():
    _p = environ_mag.usage(False)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

