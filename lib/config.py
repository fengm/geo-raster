
import logging

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

def load(f_cfg=None):
	global cfg

	import ConfigParser
	cfg = ConfigParser.ConfigParser()

	_f_cfg = detect_file(f_cfg)
	if _f_cfg:
		logging.info('loading config file ' + _f_cfg)
		cfg.read(_f_cfg)

def get_attr(section, name):
	global cfg
	return cfg.get(section, name)

def get_at(section, name):
	return get_attr(section, name)

