#!/usr/bin/env python
# encoding: utf-8

'''
File: sampling_images.py
Author: Min Feng
Version: 0.1
Create: 2013-02-27 11:27:47
Description: Retrieve values from images at the samples locations defined in the shapefile
'''
'''
Version: 0.2
Date: 2013-03-14 10:35:42
Note: updated to use fiona for shapefile reading
'''
# -*- coding: utf-8 -*-

import logging

def crs_proj(crs):
	if crs == None:
		return None

	from osgeo import osr
	_prj = osr.SpatialReference()

	_items = []
	for k, v in crs.items():
		_items.append(
			"+" + "=".join(
			filter(lambda y: y and y is not True, (k, str(v)))) )

	_crs = " ".join(_items)
	_prj.ImportFromProj4(_crs)

	return _prj

def read_value(c):
	try:
		return str(c)
	except UnicodeEncodeError:
		return None

def load_samples(f_shp, reproject):
	import fiona

	with fiona.open(f_shp, 'r') as _lyr:
		_ns = []
		for _cn in _lyr.schema['properties']:
			_ns.append(_cn)

		_prj = None
		if reproject:
			_prj = crs_proj(_lyr.crs)

		import geo_raster_ex_c
		_ss = []
		_vs = []

		import numpy as np
		_v_max = np.finfo('f').max
		_v_min = np.finfo('f').min

		for _f in _lyr:
			_vs.append([read_value(_f['properties'][_n]) for _n in _ns])

			_pt = _f['geometry']['coordinates']
			if not (_v_min <= _pt[0] <= _v_max and _v_min <= _pt[1] <= _v_max):
				print ' * skip invalid loc: %s %s' % tuple(_pt)
				continue
			_ss.append(geo_raster_ex_c.geo_point(_pt[0], _pt[1], _prj))

		return _ns, _vs, _ss

def read_image_at_locs(f_img, pts):
	import geo_raster_c

	_bnd = geo_raster_c.geo_raster.open(f_img).get_band()

	_vs = []
	for _pt in pts:
		_pp = _pt
		if _pp.proj and _bnd.proj:
			_pp = _pp.project_to(_bnd.proj)

		_vv = None
		try:
			_vv = _bnd.read_location(_pp.x, _pp.y)
		except IndexError:
			logging.error('failed to read location: %s,%s' % (_pp.x, _pp.y))
			_ccc, _rrr = _bnd.to_cell(_pp.x, _pp.y)
			logging.error('size: %s,%s ;col,row: %s,%s' % (_bnd.width,
				_bnd.height, _ccc, _rrr))

		_vs.append(_vv)

	return _vs

def output_csv(ns, ss, vs, ps, f):
	"""output selected samples to CSV file"""
	_ks = ps.keys()
	_ks.sort()

	_cs = 0
	with open(f, 'w') as _f:
		_ls = [','.join(['x', 'y'] + ns + _ks)]
		for _a in xrange(len(ss)):
			_vs = ['%s' % _v for _v in [ss[_a].x, ss[_a].y] \
					+ vs[_a]] + ['%s' % ps[_k][_a] for _k in _ks]
			_vs = [(_v if (',' not in _v) else ('"%s"' % _v)) for _v in _vs]

			_ls.append(','.join(_vs))

			if len(_ls) > 100:
				if _cs > 0:
					_f.write('\n')

				_f.write('\n'.join(_ls))
				_ls = []
				_cs += 1

		if len(_ls) > 0:
			if _cs > 0:
				_f.write('\n')
			_f.write('\n'.join(_ls))

def retrieve_samples_locs(ns, vs, ss, f_imgs, f_out):
	if len(ss) == 0:
		print ' * no sample collected'
		return

	import progress_percentage
	_ppp = progress_percentage.progress_percentage(len(f_imgs))

	import os
	_ps = {}

	for _f in f_imgs:
		_ppp.next(count=True, message=os.path.basename(_f))
		logging.debug('read from ' + _f)

		_vv = read_image_at_locs(_f, ss)
		_id = os.path.basename(_f)
		_ps[_id] = _vv

	_ppp.done()

	output_csv(ns, ss, vs, _ps, f_out)

def retrieve_samples_shp(f_shp, f_imgs, f_out, reproject):
	"""retrieve values from images at the locations provided by a shapefile"""
	import os

	print 'loading sample locations from', os.path.basename(f_shp)
	_ns, _vs, _ss = load_samples(f_shp, reproject)
	print 'found %s samples' % len(_ss)

	retrieve_samples_locs(_ns, _vs, _ss, f_imgs, f_out)
	print 'output file', f_out

def find_images_in_dir(d_img):
	import os

	if os.path.isfile(d_img):
		return d_img,

	print 'search', d_img, '...'
	_fs = []
	for _root, _dirs, _files in os.walk(d_img):
		for _file in _files:
			if _file[-4:].lower() in ['.tif', '.img']:
				_fs.append(os.path.join(_root, _file))
				print '+', _fs[-1]

	print 'found', len(_fs), 'images'

	return _fs

def process_file(f_shp, d_img, f_out, reproject):
	_f_imgs = find_images_in_dir(d_img)

	if not len(_f_imgs):
		print ' * no image has been found'
		return

	retrieve_samples_shp(f_shp, _f_imgs, f_out, reproject)

def process_files(d_shp, d_img, d_out, reproject):
	print 'searching input sample files'
	_f_shp = []

	import os
	for _root, _dirs, _files in os.walk(d_shp):
		for _file in _files:
			if _file.lower().endswith('.shp'):
				_f_shp.append(os.path.join(_root, _file))

	if not len(_f_shp):
		print ' * no sample file has been found'
		return

	print 'found', len(_f_shp), 'sample files'

	import progress_percentage
	_ppp = progress_percentage.progress_percentage(len(_f_shp),
			'process sample files')

	import os
	os.path.exists(d_out) or os.makedirs(d_out)

	for _f in _f_shp:
		_ppp.next(count=True, message=os.path.basename(_f))

		_f_out = os.path.join(d_out, os.path.basename(_f)[:-4] + '.csv')
		process_file(_f, d_img, _f_out, reproject)

	_ppp.done()

def usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('-s', '--sample-file', dest='samplefile', required=True)
	_p.add_argument('-p', '--reproject', dest='reproject',
			action='store_true', default=False)

	return _p.parse_args()

def init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	import logging_util
	logging_util.init()

if __name__ == '__main__':
	init_env()
	_opts = usage()

	try:
		import os
		if os.path.isdir(_opts.samplefile):
			if os.path.exists(_opts.output) and os.path.isfile(_opts.output):
				raise Exception('The output should be a folder when the input is folder')
			process_files(_opts.samplefile, _opts.input, _opts.output,
					_opts.reproject)
		else:
			process_file(_opts.samplefile, _opts.input, _opts.output,
					_opts.reproject)

	except KeyboardInterrupt:
		print '\n\n* User stopped the program'
	except Exception, err:
		import traceback

		logging.error(traceback.format_exc())
		logging.error(str(err))

		print '\n\n* Error:', err

