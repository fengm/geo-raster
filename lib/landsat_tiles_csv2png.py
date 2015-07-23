#!/usr/bin/env python
# encoding: utf-8

'''
Create shapefile from a CSV file with joining a column to the Landsat
	WRS png file

Min Feng, Feb 5, 2014
'''

import logging
import matplotlib
matplotlib.use("AGG")


def cmap_discretize(cmap, N):
	if type(cmap) == str:
		cmap = matplotlib.cm.get_cmap(cmap)

	import numpy as np
	_cs = []
	for _ci in np.linspace(0, 1., N+1):
		_cs.append(cmap(1 - _ci))

	cmap = matplotlib.colors.ListedColormap(_cs, N=len(_cs))
	return cmap

def create(title=None, xlabel=None, ylabel=None, width=15, height=9, title_fontsize=20, label_fontsize=12):
	import matplotlib.figure
	from matplotlib.font_manager import FontProperties

	_fig = matplotlib.figure.Figure(figsize=(width, height), facecolor='w')
	if title:
		_fig.text(0.5, 0.95, title, horizontalalignment='center', fontproperties=FontProperties(size=title_fontsize, family='serif'))
	if ylabel:
		_fig.text(0.05, 0.5, ylabel, rotation='vertical', fontsize=label_fontsize, verticalalignment='center', weight='bold')
	if xlabel:
		_fig.text(0.5, 0.05, xlabel, fontsize=label_fontsize, horizontalalignment='center', weight='bold')

	return _fig

def save(fig, out):
	import os

	_d_out = os.path.dirname(out)
	os.path.exists(_d_out) or os.makedirs(_d_out)

	from matplotlib.backends.backend_agg import FigureCanvasAgg
	_cav = FigureCanvasAgg(fig)
	_cav.print_png(out, dpi=150)

def load_tiles(f, col=None):
	import csv_util

	_ts = {}
	for _r in csv_util.open(f):
		_t = _r.get('tile')
		if _t in _ts:
			continue

		_v = None
		if col:
			_z = _r.get(col)
			if len(_z) > 0:
				_v = float(_z)
		_ts[_t] = _v

	return _ts

def estimate_levels(ts, num):
	_vs = [_v for _v in ts if _v != None]
	if len(_vs) == 0:
		raise Exception('no valid value found')

	if len(_vs) <= num + 1:
		return _vs

	_vs.sort()

	_d = len(_vs) * 1.0 / num
	_ls = []
	for i in xrange(num):
		_p = _vs[int(_d * i)]
		if len(_ls) > 0 and _p <= _ls[-1]:
			continue

		_ls.append(_p)
	_ls.append(_vs[-1])

	print 'estimated levels:', _ls

	return _ls

def draw(f_shp, title, ts, show_val, levels, colors, f_out):
	_fig = create(title)
	_plt = _fig.add_axes((0, 0, 1.0, 1.0), frameon=False)

	from mpl_toolkits.basemap import Basemap

	_map = Basemap(ax=_plt)
	_map.drawcoastlines(linewidth=0.25)
	_map.drawcountries(linewidth=0.25)
	_map.fillcontinents(color='#E1E1E1',lake_color='#97DBF2')
	_map.drawmapboundary(fill_color='#97DBF2', linewidth=0.25)

	import numpy as np
	_map.drawmeridians(np.arange(0,360,30))
	_map.drawparallels(np.arange(-90,90,30))

	_levels = levels
	if _levels == None and not show_val:
		_levels = estimate_levels(ts.values(), 5)

	from matplotlib.patches import Polygon
	_map.readshapefile(f_shp[:-4], 'data_wrs', drawbounds=False, antialiased=True)

	_color = None
	for xy, info in zip(_map.data_wrs, _map.data_wrs_info):
		_tile = info['PATHROW']
		if _tile not in ts:
			continue

		_vale = ts[_tile]
		if _vale == None:
			_plt.add_patch(Polygon(xy, fill=show_val, alpha=1.0, linewidth=0.2))
		else:
			if _color == None:
				_color = matplotlib.cm.ScalarMappable(matplotlib.colors.BoundaryNorm(_levels, len(_levels)), cmap_discretize(matplotlib.cm.get_cmap(colors), len(_levels)))
				_color.set_array(range(256))
			_plt.add_patch(Polygon(xy, facecolor=_color.to_rgba([_vale])[0], alpha=1.0, linewidth=0.2))

	if _color:
		_plt_legend = _fig.add_axes((0.1, 0.07 , 0.8, 0.07), frame_on=False)
		_plt_legend.set_axis_off()
		_fig.colorbar(_color, ax=_plt_legend, orientation='horizontal', pad=0.00, aspect=40)

	save(_fig, f_out)

def main():
	_opts = _init_env()

	_f_ref = _opts.tile_file
	if not _f_ref:
		import os, sys

		if _opts.tile_tag == 'wrs2':
			_f_ref = os.path.join(sys.path[0], 'data/landsat/wrs2_descending.shp')
		elif _opts.tile_tag == 'wrs1':
			_f_ref = os.path.join(sys.path[0], 'data/landsat/wrs1_descending.shp')
		else:
			raise Exception('unsupported tiling system tag (%s)' % _opts.tile_tag)

	import os
	draw(_f_ref, _opts.title if _opts.title else os.path.basename(_opts.input),
	  load_tiles(_opts.input, _opts.column),
	  _opts.column == None, _opts.levels, _opts.colors, _opts.output)

def _usage():
	import argparse
	import os

	_p = argparse.ArgumentParser()
	_p.add_argument('--logging', dest='logging')
	_p.add_argument('--config', dest='config')

	_p.add_argument('-i', '--input-csv', dest='input', required=True)
	_p.add_argument('-t', '--title', dest='title')

	_p.add_argument('-l', '--levels', dest='levels', nargs='+', type=float)
	_p.add_argument('--colors', dest='colors', default='jet')

	_p.add_argument('-c', '--column', dest='column')
	_p.add_argument('--tile-file', dest='tile_file')
	_p.add_argument('--tiling', dest='tile_tag', default='wrs2')
	_p.add_argument('-o', '--output-shp', dest='output')

	_opts = _p.parse_args()
	if not _opts.output:
		_opts.output = os.path.join(os.path.join(os.path.dirname(_opts.input), 'png'), os.path.basename(_opts.input)[:-4] + '.png')

	return _opts

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

