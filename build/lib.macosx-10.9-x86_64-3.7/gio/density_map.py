'''
File: density_map.py
Author: Min Feng
Version: 0.1
Create: 2014-01-03 15:49:46
Description: draw density plot for the data
'''

import logging
from . import landsat

def compare_color(c1, c2):
	return all([c1[_k] == c2[_k] for _k in range(3)])

def crop_image(f):
	import Image

	_exclude_colors = [(0, 0, 128), (0, 0, 127)]
	_color_back = (0, 0, 0, 255)

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

			if any([compare_color(_p, _t) for _t in _exclude_colors]):
				_data[_c, _r] = _color_back

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

def draw_band(fig, title, pos, mx, my, density, is_log, vmin, vmax, bins):
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

	_plt.axis([_min, _max, _min, _max])
	_plt.plot([_min, _max], [_min, _max], color='white' if density else 'yellow', linestyle='dashed',
			label='1:1', linewidth=1)

	if density:
		import numpy as np
		_hist, _xedge, _yedge = np.histogram2d(_mx, _my, bins=bins, range=[[0, 100], [0, 100]])
		logging.info('range: %s - %s' % (_hist.min(), _hist.max()))

		if is_log:
			_hist[_hist > 0] = np.log10(_hist[_hist > 0])
			logging.info('log range: %s - %s' % (_hist.min(), _hist.max()))
		else:
			_hist[_hist > 0] = (_hist[_hist > 0] + 10) / 10

		_vmin = vmin
		_vmax = vmax

		if not is_log and _vmax == None and len(mx) < 500:
			_vmax = int(_hist.max() - 0.5 * _hist.std())

		_ext = [_xedge[0], _xedge[-1], _yedge[0], _yedge[-1]]
		_img = _plt.imshow(_hist.T, extent=_ext, origin='lower', vmin=_vmin, vmax=_vmax,
				interpolation='bilinear' if len(mx) < 500 else None)

		if pos == 5:
			_axe = fig.add_axes((1.0-_bound*1.8, 0, _bound / 1.5, 0.5), frameon=False, xticks=[], yticks=[])
			fig.colorbar(_img, ax=_axe)

	else:
		_plt.scatter(_mx, _my, c='w', alpha=0.5)

	# drawLine(_plt, 1, _min, _max)
	# drawLine(_plt, 2, _min, _max)
	# drawLine(_plt, 3, _min, _max)
	# drawLine(_plt, 4, _min, _max)
	# drawLine(plt, 5, _min, _max)

def draw_band_simple(fig, title, pos, mx, my, vmin, vmax):
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

	_plt = fig.add_axes((_bound + _div_x * _col + _merge, _bound + _div_y * _row + _merge, _div_x - _merge * 2, _div_y - _merge * 2), frameon=True, axis_bgcolor='w')

	# deprecated and replaced with add_axes, which is more flexible
	# _plt = fig.add_subplot(2, 3, pos, frameon=True, axis_bgcolor='k')

	if title:
		_plt.set_title(title)

	_plt.axis([_min, _max, _min, _max])
	_plt.plot([_min, _max], [_min, _max], color='blue', linestyle='dashed',
			label='1:1', linewidth=1)

	_plt.scatter(_mx, _my, c='k', marker='.', alpha=0.3, s=30)

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

def save(fig, out, dpi=150):
	from matplotlib.backends.backend_agg import FigureCanvasAgg
	_cav = FigureCanvasAgg(fig)
	_cav.print_png(out, dpi=dpi)

def draw_bands(fig, vals, density=True, is_log=True, vmin=None, vmax=None, bins=400):
	_pos = 0
	for _band in landsat.band_vals:
		print('band', _band, len(vals[_band][0]))
		_vx = vals[_band][0]
		_vy = vals[_band][1]

		draw_band(fig, landsat.band_txts[landsat.band_vals.index(_band)], _pos, _vx, _vy, density, is_log, vmin, vmax, bins)
		_pos += 1

def draw_bands_simple(fig, vals, vmin=None, vmax=None):
	_pos = 0
	for _band in landsat.band_vals:
		print('band', _band, len(vals[_band][0]))
		_vx = vals[_band][0]
		_vy = vals[_band][1]

		draw_band_simple(fig, landsat.band_txts[landsat.band_vals.index(_band)], _pos, _vx, _vy, vmin, vmax)
		_pos += 1

if __name__ == '__main__':
	pass

