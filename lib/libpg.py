'''
File: libpg.py
Author: Min Feng
Version: 0.1
Create: 2016-08-16 22:22:07
Description: the library provides functions for connecting and visiting postgresql database
'''

import psycopg2
import logging

class obj(dict):

	def __init__(self, **w):
		super(obj, self).__init__(**w)

	def __getattr__(self, name):
		return super(obj, self).__getitem__(name)

	def __setattr__(self, name, value):
		return super(obj, self).__setitem__(name, value)

	def __str__(self):
		_ls = []
		for _k, _v in list(self._obj.items()):
			_ls.append('%15s: %s' % (_k, _v))
		return '\n'.join(_ls)

class table:

	def __init__(self, cur, name):
		self._cur = cur
		self._name = name

	def insert(self, vals):
		_ks = list(vals.keys())

		_sql = 'INSERT INTO %s (%s) VALUES (%s)' % (self._name, ','.join(_ks), \
				','.join(['%s' for i in range(len(_ks))]))
		return self._cur.execute(_sql, [vals[_k] for _k in _ks])

	def select(self, where='TRUE', vals=None):
		_sql = 'SELECT * FROM %s WHERE %s' % (self._name, where)

		_vals = vals
		if isinstance(_vals, str):
			_vals = (_vals, )

		self._cur.execute(_sql, tuple(_vals) if _vals else None)

		_cols = [_d[0] for _d in self._cur._cur.description]
		for _r in self._cur._cur.fetchall():
			_obj = obj()
			for _i in range(len(_cols)):
				_obj[_cols[_i]] = _r[_i]

			yield _obj

	def delete(self, where, vals=None):
		_vals = vals
		if isinstance(_vals, str):
			_vals = (_vals, )

		_sql = 'DELETE FROM %s WHERE %s' % (self._name, where)
		return self._cur.execute(_sql, tuple(_vals) if _vals else None)

class _cursor():

	def __init__(self, cur):
		self._cur = cur

	def __enter__(self):
		logging.info('receiving DB cursor')
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		logging.info('closing DB cursor')
		self._cur.close()

	def execute(self, oper, pars=None):
		return self._cur.execute(oper, pars)

	def fetchone(self):
		return self._cur.fetchone()

	def fetchall(self):
		return self._cur.fetchone()

	def close(self):
		return self._cur.close()

	def seq(self, name):
		self._cur.execute('select nextval(\'%s\')' % name)
		return self._cur.fetchone()[0]

	def table(self, name):
		return table(self, name)

class _connect():

	def __init__(self, **kwargs):
		logging.info('connect to DB')
		self._con = psycopg2.connect(**kwargs)

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		logging.info('closing DB connection')
		self._con.close()

	def cursor(self):
		logging.info('create DB cursor')
		return _cursor(self._con.cursor())

	def close(self):
		self._con.close()

	def commit(self):
		self._con.commit()

def connect(host=None, database=None, user=None, password=None):
	from . import config
	import logging

	logging.info('create DB connection')
	# return psycopg2.connect(host=config.cfg.get('pg', 'host'),
	# 		database=config.cfg.get('pg', 'database'),
	# 		user=config.cfg.get('pg', 'user'),
	# 		password=config.cfg.get('pg', 'password'))
	return _connect(host=host or config.cfg.get('pg', 'host'),
			database=database or config.cfg.get('pg', 'database'),
			user=user or config.cfg.get('pg', 'user'),
			password=password or config.cfg.get('pg', 'password'))

