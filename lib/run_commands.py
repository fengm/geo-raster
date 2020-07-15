#!/usr/bin/env python
# encoding: utf-8

def run_exe(cmd, shell=True):
	import logging
	logging.debug('run cmd: ' + str(cmd))

	_shell = shell
	if type(cmd) == tuple or type(cmd) == list:
		_shell = False

	import subprocess
	_p = subprocess.Popen(cmd, shell=_shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	_rs = _p.communicate()

	logging.debug('return code: %s' % _p.returncode)
	if _p.returncode != 0:
		import logging
		logging.error('Failed running cmd: %s %s\n' % (cmd, _p.returncode))
		logging.error('Output message: %s\n' % _rs[0])
		logging.error('Error message: %s' % _rs[1])
		raise Exception('Failed running cmd: ' + str(cmd))

	if _rs == None or len(_rs) == 0:
		return None
	return _rs

def run(cmd, shell=True, cwd=None, env=None, stdout=None, stderr=None, raise_exception=True, debug=False, check=True):
	import logging

	_shell = shell
	if type(cmd) == tuple or type(cmd) == list:
		_shell = False

	logging.info('run %scmd: "%s"' % ('shell ' if _shell else '', str(cmd)))

	import subprocess
	_stdout = stdout if stdout else subprocess.PIPE
	_stderr = stderr if stderr else subprocess.PIPE

	if cwd:
		logging.debug('cwd: %s' % cwd)
	if env:
		logging.debug('env: %s' % str(env))

	_p = subprocess.Popen(cmd, shell=_shell, stdout=_stdout, stderr=_stderr, cwd=cwd, env=env)
	_rs = list(_p.communicate())

	if _rs == None:
		_rs = []

	for i in range(2 - len(_rs)):
		_rs.append(None)

	_to_t = lambda x: x.decode('utf-8') if x is not None else x
	_rs = [_to_t(_r) for _r in _rs]

	import logging
	from . import config
	
	logging.info('return code: %s' % _p.returncode)

	# if check and _p.returncode != 0:
	if raise_exception and _p.returncode != 0:
		_debug = debug or config.getboolean('conf', 'debug')
		
		if _debug and _rs[0]:
			logging.info('Output message:%s\n' % _rs[0])
			
		if _debug and _rs[1]:
			logging.warning('Error message:%s' % _rs[1])
			
		raise Exception('Failed with cmd (%s): %s' % (_p.returncode, str(cmd)))

	return _p.returncode, _rs[0], _rs[1]
		
# def initGDAL():
# 	import os

# 	_gdal_dir = os.path.join(sys.path[0], 'gdal')
# 	_gdal_bin = os.path.join(_gdal_dir, 'bin')

# 	if _gdal_bin not in os.environ['PATH']:
# 		os.environ['PATH'] = _gdal_bin + ';' + os.environ['PATH']

# 	if 'GDAL_DATA' not in os.environ:
# 		os.environ['GDAL_DATA'] = os.path.join(_gdal_dir, 'data')

# def unzipGz(fin, fout):
# 	import gzip

# 	_t = open(fout, 'wb')
# 	_z = gzip.GzipFile(fin)

# 	print('Unzip', fin, end=' ')

# 	_ll = 1024 * 1024 * 100
# 	while True:
# 		_buf = _z.read(_ll)

# 		if len(_buf) > 0:
# 			_t.write(_buf)
# 			print('.', end=' ')
# 		else:
# 			break

# 	print('done')

# def rasterCellSize(f):
# 	import os, re

# 	initGDAL()

# 	_out = os.popen('gdalinfo %s' % f)
# 	_txt = _out.read()
# 	_out.close()

# 	_m = re.search('Pixel Size = \((\d+\.?\d*),\-?\d+\.?\d*\)', _txt, re.M)
# 	if _m:
# 		return float(_m.group(1))

# 	raise IOError('Failed to find cell size information')

# def executeJavaClass(cls, params = None):
# 	import sys, os, string

# 	_pp = sys.argv[1:]
# 	if params:
# 		_pp = params

# 	_jars = ['.', os.path.join(sys.path[0], 'cls')] + [os.path.join(os.path.join(sys.path[0], 'lib'), _f) for _f in os.listdir(os.path.join(sys.path[0], 'lib')) if _f.lower().endswith('.jar')]

# 	_spliter = ';'
# 	if os.name == 'posix':
# 		_spliter = ':'

# 	_code = os.system('java -Xmx1400m -Djava.util.logging.config.file=' + os.path.join(os.path.join(sys.path[0], 'conf'), 'glcf.logging.properties') + ' -cp ' + string.join(_jars, _spliter) + ' ' + cls + ' ' + string.join(['"' + _p + '"' for _p in _pp], ' '))
# 	if _code == 33280:
# 		print('Stopped by user')
# 		sys.exit()

# 	return _code

# if __name__ == '__main__':
# 	import sys
# 	if len(sys.argv) > 2:
# 		if len(sys.argv) > 3:
# 			executeJavaClass(sys.argv[1], sys.argv[2:])
# 		else:
# 			executeJavaClass(sys.argv[1])

