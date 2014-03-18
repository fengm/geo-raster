'''
File: density_map.py
Author: Min Feng
Version: 0.1
Create: 2014-01-03 15:49:46
Description: draw density plot for the data
'''

import logging
import landsat

def crop_image(f):
	import Image

	_im = Image.open(f)
	_data = _im.load()

	_w, _h = _im.size
	_min_x = _w
	_max_x = 0
	_min_y = _h
	_max_y = 0

	for _r in range(_h):
		for _c in range(_w):
			_p = _data[_c, _r]

			if _p[0] != 255 and _p[1] != 255 and _p[2] != 255:
				_min_x = min(_min_x, _c)
				_min_y = min(_min_y, _r)
				_max_x = max(_max_x, _c)
				_max_y = max(_max_y, _r)

			if _p[0] == 0 and _p[1] == 0 and _p[2] == 128:
				_data[_c, _r] = (0, 0, 0, 255)
			elif _p[0] == 0 and _p[1] == 0 and _p[2] == 127:
				_data[_c, _r] = (0, 0, 0, 255)

	_im.crop((_min_x - 2, _min_y - 2, _max_x + 2, _max_y + 2)).save(f, "PNG")

def draw_line(plt, scale, min, max):
	plt.plot([min, max], [min - scale * (0.005 + 0.05 * min), max - scale * (0.005 + 0.05 * max)], color='gray', linestyle='dashed', label='1:1', linewidth=0.3)
	plt.plot([min, max], [min + scale * (0.005 + 0.05 * min), max + scale * (0.005 + 0.05 * max)], color='gray', linestyle='dashed', label='1:1', linewidth=0.3)

# def drawChart(fig, title, mx, my, bins='log', vmin=0, vmax=3, gridsize=400):
# 	_range = [0, 100, 0]
#
# 	_min = _range[0] - _range[2]
# 	_max = _range[1] + _range[2]
#
# 	_mx = mx
# 	_my = my
#
# 	if title:
# 		plt.title(title)
# 	plt.autoscale(enable=True, axis='both')
# 	plt.hexbin(_mx, _my, bins=bins, gridsize=gridsize, extent=[_min, _max, _min, _max], marginals=False, vmax=vmax, vmin=vmin)
# 	plt.plot([_min, _max], [_min, _max], color='white', linestyle='dashed', label='1:1', linewidth=1)

def draw_band(fig, title, pos, mx, my, is_log, vmin, vmax, bins):
	_range = [0, 100, 0]

	_min = _range[0] - _range[2]
	_max = _range[1] + _range[2]

	_mx = mx
	_my = my

	_cols = 3
	_rows = 2

	_col = pos % _cols
	# revert the rows because the y coordinate starts from the bottom
	_row = (_rows - pos // _cols) - 1

	_bound = 0.08
	_space = 1.0 - _bound * 2
	_merge = 0.03

	_div_x = _space / _cols
	_div_y = _space / _rows

	_plt = fig.add_axes((_bound + _div_x * _col + _merge, _bound + _div_y * _row + _merge, _div_x - _merge * 2, _div_y - _merge * 2), frameon=True, axis_bgcolor='k')

	# deprecated and replaced with add_axes, which is more flexible
	# _plt = fig.add_subplot(2, 3, pos, frameon=True, axis_bgcolor='k')

	if title:
		_plt.set_title(title)

	import numpy as np
	_hist, _xedge, _yedge = np.histogram2d(_mx, _my, bins=bins, range=[[0, 100], [0, 100]])
	logging.info('range: %s - %s' % (_hist.min(), _hist.max()))

	if is_log:
		_hist = np.log10(_hist)
		logging.info('log range: %s - %s' % (_hist.min(), _hist.max()))

	_ext = [_xedge[0], _xedge[-1], _yedge[0], _yedge[-1]]
	_img = _plt.imshow(_hist.T, extent=_ext, origin='lower', vmin=vmin, vmax=vmax)

	# _plt.hexbin(_mx, _my, bins=bins, gridsize=gridsize, extent=[_min, _max, _min, _max], marginals=False, vmax=vmax, vmin=vmin)

	if pos == 5:
		_axe = fig.add_axes((1.0-_bound*1.8, 0, _bound / 1.5, 0.5), frameon=False, xticks=[], yticks=[])
		fig.colorbar(_img, ax=_axe)

	_plt.axis([_min, _max, _min, _max])
	_plt.plot([_min, _max], [_min, _max], color='white', linestyle='dashed', label='1:1', linewidth=1)

	# drawLine(_plt, 1, _min, _max)
	# drawLine(_plt, 2, _min, _max)
	# drawLine(_plt, 3, _min, _max)
	# drawLine(_plt, 4, _min, _max)
	# drawLine(plt, 5, _min, _max)

def removeEnd(x):
	if x.endswith('\\') or x.endswith('/'):
		return x[:-1]

	return x

def create(title, xlabel, ylabel, width=15, height=9, title_fontsize=14, label_fontsize=12):
	import matplotlib.figure
	from matplotlib.font_manager import FontProperties

	_fig = matplotlib.figure.Figure(figsize=(width, height), facecolor='w')
	if title:
		_fig.text(0.5, 0.95, title, horizontalalignment='center', fontproperties=FontProperties(size=title_fontsize))
	if ylabel:
		_fig.text(0.05, 0.5, ylabel, rotation='vertical', fontsize=label_fontsize, verticalalignment='center', weight='bold')
	if xlabel:
		_fig.text(0.5, 0.05, xlabel, fontsize=label_fontsize, horizontalalignment='center', weight='bold')

	return _fig

def save(fig, out):
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	_cav = FigureCanvasAgg(fig)
	_cav.print_png(out, dpi=150)

def draw_bands(fig, vals, is_log=True, vmin=None, vmax=None, bins=400):
	_pos = 0
	for _band in landsat.band_vals:
		print 'band', _band, len(vals[_band][0])
		_vx = vals[_band][0]
		_vy = vals[_band][1]

		draw_band(fig, landsat.band_txts[landsat.band_vals.index(_band)], _pos, _vx, _vy, is_log, vmin, vmax, bins)
		_pos += 1

if __name__ == '__main__':
	pass

