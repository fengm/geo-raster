'''
File: config.py
Author: Min Feng
Version: 0.1
Create: 2014-03-18 02:02:29
Description: help locate and read the configuration file
'''
import logging
import collections

cfg = None

def _detect_sys(f, ext):
	import os
	import sys

	_f = f + (ext if ext.startswith('.') else ('.' + ext))

	_f_cfg = os.path.join(sys.argv[0], _f)
	if os.path.exists(_f_cfg):
		return _f_cfg

	_f_cfg = os.path.join(sys.path[0], 'conf', _f)
	if os.path.exists(_f_cfg):
		return _f_cfg

	_f_cfg = os.path.join(sys.path[0], 'etc', _f)
	if os.path.exists(_f_cfg):
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

	_f = _detect_sys(_f, 'conf') or _detect_sys(_f, 'ini')
	return _f

def load(f_cfg=None, defaults=None, dict_type=collections.OrderedDict, allow_no_value=False):
	global cfg

	import sys
	_defaults = {'root': sys.path[0]}
	defaults != None and _defaults.update(defaults)

	import ConfigParser
	cfg = ConfigParser.ConfigParser(_defaults, dict_type, allow_no_value)

	_fs = []
	for _f in (f_cfg if (isinstance(f_cfg, list) or isinstance(f_cfg, tuple)) else [f_cfg]):
		_l = _detect_file(_f)
		if _l == None:
			continue

		logging.info('loading config file ' + _l)
		_fs.append(_l)

	cfg.read(_fs)

def get_attr(section, name):
	global cfg
	return cfg.get(section, name)

def get_at(section, name):
	return get_attr(section, name)

def items(section):
	global cfg

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

