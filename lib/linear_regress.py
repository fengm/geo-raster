
'''
File: regression.py
Author: Min Feng
Version: 0.1
Create: 2013-01-19 17:02:13
Description: module for linear regression
'''

def linear_regress_ols(xs, ys):
	'''
	calculate linear regression using OLS
	return <intercept> <slope> <R2>
	'''

	if len(xs) == 0 or len(xs) != len(ys):
		raise Exception('error in input data')

	_mx = sum(xs) / len(xs)
	_my = sum(ys) / len(ys)

	_s_xy = cal_sxy(xs, ys)
	_s_xx = cal_s(xs)

	if _s_xx == 0:
		raise Exception('linear regression failed because variance for X is zero')

	_s_yy = cal_s(ys)

	_b1 = _s_xy / _s_xx
	_b0 = _my - _b1 * _mx

	_r2 = (_s_xy ** 2) / (_s_xx * _s_yy)

	return _b0, _b1, _r2

def linear_regress_rma(xs, ys):
	'''
	calculate linear regression using RMA (reduced major axis)
	return <intercept> <slope> <R2>
	'''

	if len(xs) < 2 or len(xs) != len(ys):
		raise Exception('error in input data')

	_mx = sum(xs) / len(xs)
	_my = sum(ys) / len(ys)

	_s_xy = cal_sxy(xs, ys)
	_s_xx = cal_s(xs)
	_s_yy = cal_s(ys)

	if _s_xx == 0:
		raise Exception('linear regression failed because variance for X is zero')

	_b1 = sign(_s_xy) * (_s_yy / _s_xx) ** 0.5
	_b0 = _my - _b1 * _mx

	_r2 = (_s_xy ** 2) / (_s_xx * _s_yy)

	return _b0, _b1, _r2

def sign(v):
	if v == 0 or v == -0:
		return 0
	if v > 0:
		return 1
	return -1

def load_data():
	import sys, os

	_ls = [_l.split('\t') for _l in \
			open(os.path.join(sys.path[0], 'data.txt')).read().splitlines()]

	_xs = [float(_v[0]) for _v in _ls]
	_ys = [float(_v[1]) for _v in _ls]

	return _xs, _ys

def cal_sxy(xs, ys):
	_mx = sum(xs) / len(xs)
	_my = sum(ys) / len(ys)

	_v = 0.0
	for i in range(len(xs)):
		_v += (ys[i] - _my) * (xs[i] - _mx)

	return _v / (len(xs) - 1)

def cal_s(vs):
	_mx = sum(vs) / len(vs)

	_v = 0.0
	for i in range(len(vs)):
		_v += (vs[i] - _mx) ** 2

	return _v / (len(vs) - 1)

if __name__ == '__main__':
	_xs, _ys = load_data()

	_b0, _b1, _r2 = linear_regress_ols(_xs, _ys)
	print('y = %fx + %f, r2:%f' % (_b1, _b0, _r2))

	_b0, _b1, _r2 = linear_regress_ols(_ys, _xs)
	print('y = %fx + %f, r2:%f' % (_b1, _b0, _r2))

	_b0, _b1, _r2 = linear_regress_rma(_xs, _ys)
	print('y = %fx + %f, r2:%f' % (_b1, _b0, _r2))

	_b0, _b1, _r2 = linear_regress_rma(_ys, _xs)
	print('y = %fx + %f, r2:%f' % (_b1, _b0, _r2))
