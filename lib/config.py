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
		_m = re.match('(.+)\.[^\.]+$', _f)
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

	import sys
	_defaults = {'root': sys.path[0]}
	defaults != None and _defaults.update(defaults)

	import ConfigParser
	cfg = ConfigParser.ConfigParser(_defaults, dict_type, allow_no_value)

	import os
	_fs = []
	for _f in (f_cfg if (isinstance(f_cfg, list) or isinstance(f_cfg, tuple)) else [f_cfg]):
		if _f and os.path.exists(_f):
			if os.path.isdir(_f):
				_fs.extend(_load_dir(_f))
				continue

			if os.path.splitext(_f)[-1] in ['.txt']:
				_fs.extend(_load_file(_f))
				continue

		_l = _detect_file(_f)
		if _l == None:
			continue

		_fs.append(_l)

	for _l in _fs:
		logging.info('loading config file: %s' % _l)

	cfg.read(_fs)

def get_attr(section, name):
	global cfg
	return cfg.get(section, name)

def get_at(section, name):
	return get_attr(section, name)

def items(section):
	global cfg

	if section not in cfg.sections():
		return

	_ns = cfg.defaults()
	for _n, _v in cfg.items(section):
		if _n in _ns:
			continue

		yield _n, _v

def get(section, name, val=None):
	"""get config param

	:section: section
	:name: option name
	:val: default value
	:returns: config value

	"""
	global cfg

	if not cfg.has_option(section, name):
		return val

	return cfg.get(section, name)

def getint(section, name, val=None):
	"""get config param

	:section: section
	:name: option name
	:val: default value
	:returns: config value

	"""
	global cfg

	if not cfg.has_option(section, name):
		return val

	return cfg.getint(section, name)

def getfloat(section, name, val=None):
	"""get config param

	:section: section
	:name: option name
	:val: default value
	:returns: config value

	"""
	global cfg

	if not cfg.has_option(section, name):
		return val

	return cfg.getfloat(section, name)

def getboolean(section, name, val=None):
	"""get config param

	:section: section
	:name: option name
	:val: default value
	:returns: config value

	"""
	global cfg

	if not cfg.has_option(section, name):
		return val

	return cfg.getboolean(section, name)

def has_option(section, name):
	"""get config param

	:section: section
	:name: option name
	:val: default value
	:returns: config value

	"""
	global cfg
	return cfg.has_option(section, name)

