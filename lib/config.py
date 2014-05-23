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

def detect_file(f_cfg):
	import os, sys, re

	if f_cfg:
		return f_cfg

	_f = os.path.basename(sys.argv[0])
	_m = re.match('(.+)\.[^\.]+$', _f)

	if _m:
		_f = _m.group(1)
	_f += '.conf'

	_f_cfg = os.path.join(sys.argv[0], _f)
	if os.path.exists(_f_cfg):
		return _f_cfg

	_f_cfg = os.path.join(sys.path[0], 'conf', _f)
	if os.path.exists(_f_cfg):
		return _f_cfg

	return None

def load(f_cfg=None, defaults=None, dict_type=collections.OrderedDict, allow_no_value=False):
	global cfg

	import sys
	_defaults = {'root': sys.path[0]}
	defaults != None and _defaults.update(defaults)

	import ConfigParser
	cfg = ConfigParser.ConfigParser(_defaults, dict_type, allow_no_value)

	_f_cfg = detect_file(f_cfg)
	if _f_cfg:
		logging.info('loading config file ' + _f_cfg)
		cfg.read(_f_cfg)

def get_attr(section, name):
	global cfg
	return cfg.get(section, name)

def get_at(section, name):
	return get_attr(section, name)

