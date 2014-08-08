'''
File: multi_task.py
Author: Min Feng
Version: 0.1
Create: 2013-04-03 15:54:01
Description: processing with multiple instances
'''
import multiprocessing
import Queue, signal
import logging

def add_task_opts(p):
	p.add_argument('-in', '--instance-num', dest='instance_num', type=int, default=1)
	p.add_argument('-ip', '--instance-pos', dest='instance_pos', type=int, default=0)
	p.add_argument('-ts', '--task-num', dest='task_num', type=int, default=1)

def load_from_list(f_ls, opts):
	return load_list(f_ls, opts.instance_num, opts.instance_pos)

def load_list(f_ls, num, pos):
	logging.debug('loading ' + f_ls)

	with open(f_ls) as _fi:
		_ls_a = _fi.read().splitlines()
		_ls_a = [_l.strip() for _l in _ls_a if _l.strip()]
		_ls_s = [_ls_a[i] for i in xrange(pos, len(_ls_a), num)]
		logging.debug('select %s from %s' % (len(_ls_s), len(_ls_a)))

		return _ls_s

def load_ids(size, num, pos):
	logging.debug('loading ids %d' % size)
	return xrange(pos, size, num)

def text(t):
	import sys
	sys.stdout.write(t)
	sys.stdout.flush()

def print_percent(nu, tn, perc_step, end=False):
	_ss = 100.0
	_p1 = int((nu-1) * _ss // (perc_step * tn))
	_p2 = int((nu+0) * _ss // (perc_step * tn))

	if end:
		logging.info('--> finished task %d %d' % (nu, tn))
	else:
		logging.info('<-- start task %d %d' % (nu, tn))

	if _p1 < _p2:
		if end:
			text('\r+ \t\t\t|  %3.1f%%(%d/%d)     ' % (_p2 * perc_step, nu, tn))
		else:
			text('\r+ %3.1f%%(%d/%d)     ' % (_p2 * perc_step, nu, tn))
		# if end:
		# 	print '--> %3d/%d,%3d%%\r' % (nu, tn, _p2 * perc_step)
		# else:
		# 	print '<-- %3d/%d,%3d%%\r' % (nu, tn, _p2 * perc_step)

def work_function(obj, job_queue, vs, mag, res, t_lock):
	signal.signal(signal.SIGINT, signal.SIG_IGN)

	while (not job_queue.empty()) and (mag['num_done'] <= len(obj.args)):
		try:
			if mag['stop']:
				return

			with t_lock:
				mag['num_load'] += 1

				_nu = mag['num_load']
				print_percent(_nu, len(obj.args), obj.perc_step)

				_ts = job_queue.get(block=False)

			_ps = tuple(_ts) + tuple(vs)
			logging.info('task (%s) params: %s' % (_nu, ','.join([str(_v) for _v in _ps])))

			if mag['stop']:
				return

			_rs = None
			try:
				_rs = obj.func(*_ps)
			except KeyboardInterrupt:
				mag['stop'] = True
				print '\n\n* User stopped the program'
				return
			except Exception, err:
				if not obj.continue_exception:
					mag['stop'] = True
					return

				import traceback

				logging.error(traceback.format_exc())
				logging.error('Error (%s): %s' % (_nu, str(err)))

				print '\n\n* Error:', err
				continue

			if mag['stop']:
				return

			res.append(_rs)
			logging.info('task (%s) end' % _nu)

			# print the progress percentage
			with t_lock:
				_nu = mag['num_done'] + 1
				mag['num_done'] = _nu
				print_percent(_nu, len(obj.args), obj.perc_step, end=True)

		except Queue.Empty:
			break

class Pool:
	def __init__(self, func, args, t_num, continue_exception=False, perc_step=0.1):
		assert t_num > 0

		self.func = func
		self.args = args
		self.t_num = min(int(t_num), len(args))
		self.perc_step = perc_step

	def run(self, vs=()):
		logging.info('process tasks (%d, %d)' % (len(self.args), self.t_num))

		_mag = multiprocessing.Manager().dict()
		_mag['stop'] = False
		_mag['num_load'] = 0
		_mag['num_done'] = 0
		_mag['out'] = []
		_out = multiprocessing.Manager().list()
		_lock = self.create_lock()

		# exit if there is no task
		if len(self.args) <= 0:
			return

		# call the run_single() when there is only one task
		if len(self.args) == 1 or self.t_num <= 1:
			return self.run_single(vs)

		_jobs = multiprocessing.Queue()
		for _arg in self.args:
			_jobs.put(_arg if isinstance(_arg, list) or isinstance(_arg, tuple) else (_arg,))

		_jobs_num = len(self.args)
		_procs = []

		for i in range(self.t_num):
			if _mag['stop']:
				break

			_proc = multiprocessing.Process(target=work_function,
						args=(self, _jobs, vs, _mag, _out, _lock))
			_proc.start()
			_procs.append(_proc)

			import time
			time.sleep(0.1)

		try:
			_task_num = 0
			while True:
				# _pos = 0
				_task_tmp = len([_p for _p in _procs if _p != None])
				if _task_num != _task_tmp:
					logging.info('Alive tasks num: %s' % _task_tmp)
					_task_num = _task_tmp

					if _task_num <= 0:
						break

				for _idx in xrange(len(_procs)):
					_proc = _procs[_idx]
					if _proc == None:
						continue

					_proc.join(0.1)
					if _proc.is_alive() == False:
						_procs[_idx] = None

				if _mag['stop'] or (len(_out) >= _jobs_num and _jobs.empty()):
					for _proc in _procs:
						if _proc == None:
							continue
						_proc.terminate()
					break

			# print_percent(len(self.args), len(self.args), True)
			print ''

			_rs = []
			for _oo in _out:
				_rs.append(_oo)

			# while not _results.empty():
			# 	_rs.append(_results.get())
			return _rs

		except KeyboardInterrupt:
			logging.warning('terminated by user')
			print 'parent received ctrl-c'
			for _proc in _procs:
				if _proc == None:
					continue
				_proc.terminate()
				# _proc.join()

		except Exception, err:
			import traceback

			logging.error(traceback.format_exc())
			logging.error(str(err))

			print '\n\n* error:', err
			# for _proc in _procs:
			# 	_proc.terminate()
			# 	_proc.join()

		return None

	def run_single(self, vs=()):
		logging.info('process tasks (%d) without parallel' % (len(self.args)))

		self.reset_count()

		_rs = []; _pos = 0
		for _arg in self.args:
			print_percent(_pos, len(self.args), self.perc_step)
			_vs = _arg if isinstance(_arg, list) or isinstance(_arg, tuple) else (_arg,)

			_rs.append(self.func(*(tuple(_vs) + tuple(vs))))
			_pos += 1

		return _rs

	def create_lock(self):
		return multiprocessing.Lock()


