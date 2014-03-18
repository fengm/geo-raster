#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: map_raster_file.py
Author: Min Feng
Version: 0.1
Create: 2014-02-18 18:24:51
Description: create PNG map for raster file
'''

from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtXml import *
from qgis.gui import *

def reproject_shp(f_shp, bnd, fzip):
	import os
	import run_commands

	_f_out = fzip.generate_file('', '.shp')

	_ext = bnd.extent()
	_ext = ['%s' % _v for _v in [_ext.xMinimum(), _ext.yMinimum(), _ext.xMaximum(), _ext.yMaximum()]]

	# _cmd = ['ogr2ogr', '-t_srs', bnd.crs().toProj4(), '-skipfailures', '-clipdst'] + _ext + [_f_out, f_shp]
	_cmd = ['ogr2ogr', '-t_srs', bnd.crs().toProj4(), '-skipfailures'] + [_f_out, f_shp]
	# print 'cmd', ' '.join(_cmd)

	_res = run_commands.run(_cmd, False)
	if _res[0] != 0:
		print '* Failed'
		print _res[1]
		print _res[2]

		import sys
		sys.exit(_res[0])

	_f_qml = f_shp[:-3] + 'qml'
	if os.path.exists(_f_qml):
		import shutil
		shutil.copy(_f_qml, _f_out[:-3] + 'qml')

	return _f_out

def load_xml(f_sld):
	import os
	print 'loading STD', f_sld, os.path.exists(f_sld)
	_xml = QFile(f_sld)
	_xml.open(QIODevice.ReadOnly)

	_doc = QDomDocument()
	_doc.setContent(_xml)
	_xml.close()
	_nod = _doc.documentElement()

	print _nod.nodeName()

	return _nod

class vector_file:

	def __init__(self, name, path, color=None, style=None, color_border=None, style_border=None, width_border=None):
		self.name = name
		self.path = path
		self.color = color
		self.style = style
		self.color_border = color_border
		self.style_border = style_border
		self.width_border = width_border

	def load(self, bnd, fzip):
		print 'loading', self.path
		_lyr = QgsVectorLayer(reproject_shp(self.path, bnd, fzip), self.name, 'ogr')
		assert(_lyr.isValid())

		_prop = {}

		if self.color != None:
			_prop['color'] = self.color

		if self.style != None:
			_prop['style'] = self.style

		if self.color_border != None:
			_prop['color_border'] = self.color_border

		if self.style_border != None:
			_prop['style_border'] = self.style_border

		if self.width_border != None:
			_prop['width_border'] = str(self.width_border)

		_lyr.setRendererV2(QgsSingleSymbolRendererV2(QgsFillSymbolV2.createSimple(_prop)))
		QgsMapLayerRegistry.instance().addMapLayer(_lyr)

		return _lyr

class vector_style:
	def __init__(self, name, path, f_sld=None):
		self.name = name
		self.path = path
		self.f_sld = f_sld

	def load(self, bnd, fzip):
		print 'loading', self.path
		_lyr = QgsVectorLayer(reproject_shp(self.path, bnd, fzip), self.name, 'ogr')
		assert(_lyr.isValid())

		print _lyr.displayField()
		# _lyr.setDisplayField('name')
		# print _lyr.displayField()
		# print '#', _lyr.hasLabelsEnabled(), _lyr.fieldNameIndex('NAME')
		# _lyr.enableLabels(True)
		# print '#', _lyr.hasLabelsEnabled()
		# print _lyr.displayField()

		if self.f_sld:
			_lyr.readXml(load_xml(self.f_sld))

		QgsMapLayerRegistry.instance().addMapLayer(_lyr)

		return _lyr

def draw_forest_map(f_shps_def, f_shps_sld, f_img, f_sld, f_out, fzip, scale=3):
	QgsApplication.setPrefixPath("/usr", True)
	QgsApplication.initQgis()

	# _app = QgsApplication([], True)

	print 'loading layers'
	_lyr_img = QgsRasterLayer(f_img)
	_lyr_img.readXml(load_xml(f_sld))
	QgsMapLayerRegistry.instance().addMapLayer(_lyr_img)

	_cols = int(_lyr_img.width() / scale)
	_rows = int(_lyr_img.height() / scale)

	print '* %s x %s (%s)' % (_cols, _rows, scale)
	_img = QImage(QSize(_cols, _rows), QImage.Format_ARGB32_Premultiplied)

	_color = QColor(200,200,200)
	_img.fill(_color.rgb())

	p = QPainter()
	p.begin(_img)
	p.setRenderHint(QPainter.Antialiasing)

	_render = QgsMapRenderer()
	print _render.labelingEngine()
	print QgsPalLabeling()
	# _render.setLabelingEngine(QgsPalLabeling())

	_ext = _lyr_img.extent()
	_render.setExtent(_ext)

	_v_lyrs_def = [_lyr.load(_lyr_img, fzip) for _lyr in f_shps_def]
	_v_lyrs_sld = [_lyr.load(_lyr_img, fzip) for _lyr in f_shps_sld]

	lst = [_lyr.id() for _lyr in _v_lyrs_sld] + [_lyr.id() for _lyr in _v_lyrs_def] + [_lyr_img.id()]
	print 'layers', len(lst)

	_render.setLayerSet(lst)

	print 'rendering map'
	_render.setOutputSize(_img.size(), _img.logicalDpiX())
	_render.render(p)
	p.end()

	print 'saving map'
	_img.save(f_out,"png")

	QgsApplication.exitQgis()
	print 'done'

def main():
	_opts = _init_env()

	_f_shp = '/home/mfeng/local/data/earth/10m_cultural/ne_10m_admin_0_countries.shp'
	_f_lon = '/home/mfeng/local/data/global/world30.shp'
	# _f_oce = '/home/mfeng/local/data/earth/10m_physical/ne_10m_ocean.shp'
	_f_oce = '/home/mfeng/local/data/earth/clean/ne_10m_ocean.shp'
	_f_lak = '/home/mfeng/local/data/earth/10m_physical/ne_10m_lakes.shp'

	_f_sld = 'conf/forest_percent.qml'
	_f_out = 'map_na.png'

	_r_lyrs_def = [
			vector_file('countries', _f_shp, None, 'no', '50,50,50,150', 'solid', 0.5),
			vector_file('grid', _f_lon, None, 'no', '100,100,100,80', 'dash'),
			vector_file('ocean', _f_oce, '0,0,200,255', 'solid', None, 'no', 0.0),
			vector_file('lake', _f_lak, '60,60,230,255', 'solid', None, 'no', 0.0)
		]

	_f_wrs1 = '/home/mfeng/local/test/glcf/fcc_1975/global_processing/fcc_1975_wrs1_test.shp'
	_f_wrs2 = '/home/mfeng/local/test/glcf/fcc_1975/global_processing/fcc_1975_wrs2.shp'

	_r_lyrs_sld = [
			vector_style('WRS1', _f_wrs1)#,
			# vector_style('WRS2', _f_wrs2)
		]

	# _f_img = 'mosaic/mss_fcc1975_na_500m.img'
	_f_img = _opts.input
	_f_out = _opts.output

	import file_unzip
	with file_unzip.file_unzip() as _zip:
		draw_forest_map(_r_lyrs_def, _r_lyrs_sld, _f_img, _f_sld, _f_out, _zip, _opts.scale)

def _usage():
	import argparse

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')

	_p.add_argument('-i', '--input', dest='input', required=True)
	_p.add_argument('-o', '--output', dest='output', required=True)
	_p.add_argument('-s', '--scale', dest='scale', type=float, default=10)

	return _p.parse_args()

def _init_env():
	import os, sys
	_d_in = os.path.join(sys.path[0], 'lib')
	if os.path.exists(_d_in):
		sys.path.append(_d_in)

	_opts = _usage()

	import logging_util
	logging_util.init(_opts.logging)

	import config
	config.load(_opts.config)

	return _opts

if __name__ == '__main__':
	main()

