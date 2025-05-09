'''
File: multi_task.py
Author: Min Feng
Version: 0.1
Create: 2013-04-03 15:54:01
Description: processing with multiple instances
'''
import multiprocessing
import queue, signal
import logging

def _default_task_pos():
    import os

    _c = 'AWS_BATCH_JOB_ARRAY_INDEX'
    if _c in os.environ:
        return int(os.environ[_c])

    return 0

def task_params(task_num=1):
    from gio import obj

    _obj = obj.obj()
    
    _obj.instance_num = 1
    _obj.instance_pos = 0
    _obj.task_num = task_num
    _obj.skip_error = True
    _obj.time_wait = 1
    _obj.task_order = 0
    _obj.task_type = 0
    _obj.use_process_temp = True

    return _obj

options=task_params

def _sagemaker_task_config():
    from . import config
    import os
    
    _f_cfg = config.get('conf', 'sagemaker_res', '/opt/ml/config/resourceconfig.json')
    if not os.path.exists(_f_cfg):
        return -1, 0

    import json
    import re
    
    with open(_f_cfg) as _fi:
        _cfg = json.load(_fi)
        _num = len(_cfg['hosts'])
        _idx = int(re.search(r'.+\-(\d+)', _cfg['current_host']).group(1)) - 1
        
        return _idx, _num

def init(opts):
    from . import config
    _tt = config.getint('conf', 'task_type')

    if _tt == 0:
        return True
        
    elif _tt == 1:
        from mpi4py import MPI

        _comm=MPI.COMM_WORLD

        _size=_comm.size
        _rank=_comm.rank

        logging.info('use MPI task pos %s/%s' % (_rank, _size))
        
    elif _tt == 2:
        _rank, _size = _sagemaker_task_config()
        if _rank < 0:
            raise Exception('failed to load SageMaker info')
            
        logging.info('use SageMaker task pos %s/%s' % (_rank, _size))
    else:
        raise Exception('unsupported task type %s' % _tt)    

    opts.instance_num = _size
    opts.instance_pos = _rank

    config.set('conf', 'instance_num', _size)
    config.set('conf', 'instance_pos', _rank)

    return True

def add_task_opts(p):
    p.add_argument('-in', '--instance-num', dest='instance_num', type=int, default=1)
    p.add_argument('-ip', '--instance-pos', dest='instance_pos', type=int, default=_default_task_pos())
    p.add_argument('-ts', '--task-num', dest='task_num', type=int, default=1)
    p.add_argument('-se', '--skip-error', dest='skip_error', default=False, action='store_true')
    p.add_argument('-tw', '--time-wait', dest='time_wait', type=int, default=1)
    p.add_argument('-to', '--task-order', dest='task_order', type=int, default=0)
    p.add_argument('-tt', '--task-type', dest='task_type', type=int, default=0, help='0: default; 1: mpi; 2: SageMaker')
    p.add_argument('--use-process-temp', dest='use_process_temp', type='bool', default=True, \
        help='use seperated temporary path for each process and clean up after each task is completed')

def _get_task_pos(opts):
    return max(0, min(opts.instance_num - 1, opts.instance_pos))

def load_from_list(f_ls, opts):
    return load_list(f_ls, opts.instance_num, _get_task_pos(opts))

def _list_sub_list(ls, opts):
    logging.debug('load sub list with type %s' % opts.task_order)

    _ls = ls
    _to = opts.task_order

    if _to < 0:
        _ls = list(reversed(_ls))
        _to = _to * -1

    if _to <= 1:
        return [_ls[i] for i in range(_get_task_pos(opts), len(_ls), opts.instance_num)]

    import math
    _nd = int(math.ceil(float(len(_ls)) / _to))

    _ss = []
    for _id in range(_get_task_pos(opts), _nd, opts.instance_num):
        _ps = _id * _to
        _ss.extend(_ls[min(len(_ls), _ps): min(_ps + _to, len(_ls))])

    return _ss

def load(ls, opts):
    import os

    if isinstance(ls, list) or isinstance(ls, tuple):
        return _list_sub_list(ls, opts)

    if isinstance(ls, str):
        from gio import file_mag
        
        _bb = file_mag.get(ls).read()
        if _bb is None:
            return []
        
        _ls = _bb.decode('utf-8').strip().splitlines()
        return _list_sub_list(_ls, opts)

    raise Exception('unsupported list type %r' % ls)

def load_list(f_ls, num, pos):
    logging.debug('loading ' + f_ls)

    with open(f_ls) as _fi:
        _ls_a = _fi.read().strip().splitlines()
        return _ls_a

def run(func, ps, opts, vs=[]):
    _pool = Pool(func, ps, opts.task_num, opts.skip_error, opts.time_wait)
    if opts.task_num == 1:
        return _pool.run_single(vs)
    else:
        return _pool.run(vs)

def load_ids(size, num, pos):
    logging.debug('loading ids %d' % size)
    return range(pos, size, num)

def text(t):
    import sys
    sys.stdout.write(t)
    sys.stdout.flush()

def create_lock():
    return multiprocessing.Lock()

def print_percent(nu, tn, perc_step, end=False):
    _ss = 100.0
    _p1 = int((nu-1) * _ss // (perc_step * tn))
    _p2 = int((nu+0) * _ss // (perc_step * tn))

    from gio import logging_util
    if end:
        logging.info('-> task end %d/%d' % (nu, tn))

        if logging_util.cloud_enabled():
            logging_util.cloud().info('-> task end %d/%d' % (nu, tn))
    else:
        logging.info('<- task start %d/%d' % (nu, tn))

        if logging_util.cloud_enabled():
            logging_util.cloud().info('-> task start %d/%d' % (nu, tn))

    if _p1 < _p2 or nu >= tn:
        if end:
            text('\r+ \t\t\t|  %3.1f%%(%d/%d)     ' % ((_p2 * perc_step) if nu < tn else 100.0, nu, tn))
        else:
            text('\r+ %3.1f%%(%d/%d)     ' % ((_p2 * perc_step) if nu < tn else 100.0, nu, tn))

def work_function(obj, job_queue, vs, mag, res, t_lock, pos):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    import time
    if obj.time_wait > 0:
        time.sleep(obj.time_wait * pos)

    while (not job_queue.empty()) and (mag['num_done'] <= len(obj.args)):
        try:
            if mag['stop']:
                return

            # with t_lock:
            with t_lock:
                mag['num_load'] += 1

                _nu = mag['num_load']
                print_percent(_nu, len(obj.args), obj.perc_step)

                _ts = job_queue.get(block=False)

            _ps = tuple(_ts) + tuple(vs)
            logging.debug('task (%s) params: %s' % (_nu, ','.join([str(_v) for _v in _ps])))

            if mag['stop']:
                return

            _rs = None

            from gio import file_unzip
            from gio import config

            try:
                _rs = obj.func(*_ps)
            except KeyboardInterrupt as _err:
                raise _err
            except Exception as _err:
                import traceback

                logging.error('Error (%s): %s' % (_nu, traceback.format_exc()))
                logging.error('Error (%s): %s' % (_nu, str(_err)))

                if obj.continue_exception:
                    continue
                else:
                    mag['stop'] = True
                    raise _err

            if config.getboolean('conf', 'use_process_temp', False):
                file_unzip.clean(file_unzip.default_dir(None), True)

            if mag['stop']:
                return

            res.append(_rs)
            # logging.info('task (%s/%s) end' % (_nu, obj.perc_step))

            # _nu = mag['num_done'] + 1
            # mag['num_done'] = _nu
            print_percent(_nu, len(obj.args), obj.perc_step, end=True)

        except queue.Empty:
            return
        finally:
            # print the progress percentage
            with t_lock:
                _nu = mag['num_done'] + 1
                mag['num_done'] = _nu
                print_percent(_nu, len(obj.args), obj.perc_step, end=True)

class Pool:
    def __init__(self, func, args, t_num, error_continue=False, time_wait=0, perc_step=0.1):
        assert t_num > 0

        self.func = func
        self.args = args
        self.t_num = min(int(t_num), len(args))
        self.perc_step = perc_step
        self.time_wait = time_wait
        self.continue_exception = error_continue

    def run(self, vs=[]):
        # logging.info('process tasks (%d, %d)' % (len(self.args), self.t_num))
        from gio import logging_util

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
                        args=(self, _jobs, vs, _mag, _out, _lock, i))
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
                    _task_num = _task_tmp

                    logging.info('alive tasks num: %s' % _task_num)
                    text('\r\t\t\t\t\t\t(%3d)' % _task_num)

                    if _task_num <= 0:
                        break

                for _idx in range(len(_procs)):
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
            print('')

            _rs = []
            for _oo in _out:
                _rs.append(_oo)

            return _rs

        except KeyboardInterrupt:
            logging.warning('terminated by user')
            print('')
            print('parent received ctrl-c')

            if logging_util.cloud_enabled():
                _log = logging_util.cloud()
                _log.warning('terminated by user')

            for _proc in _procs:
                if _proc == None:
                    continue
                _proc.terminate()
                _proc.join(5)

            while not _jobs.empty():
                _jobs.get(block=False)

        except Exception as _err:
            import traceback

            logging.error(traceback.format_exc())
            logging.error(str(_err))

            print('')
            print('* error:', _err)

            if logging_util.cloud_enabled():
                _log = logging_util.cloud()
                _log.error(traceback.format_exc())
                _log.error(str(_err))

            for _proc in _procs:
                if _proc == None:
                    continue
                _proc.terminate()
                _proc.join(5)

            while not _jobs.empty():
                _jobs.get(block=False)

        raise Exception('failed with the processing')

    def run_single(self, vs=[]):
        logging.info('process tasks (%d) without parallel' % (len(self.args)))

        from gio import logging_util
        if logging_util.cloud_enabled():
            logging_util.cloud().info('process tasks (%d) without parallel' % (len(self.args)))

        _rs = []; _pos = 0
        for _arg in self.args:
            print_percent(_pos, len(self.args), self.perc_step)
            _vs = _arg if isinstance(_arg, list) or isinstance(_arg, tuple) else (_arg,)

            if not self.continue_exception:
                _rs.append(self.func(*(tuple(_vs) + tuple(vs))))
            else:
                try:
                    _rs.append(self.func(*(tuple(_vs) + tuple(vs))))
                except KeyboardInterrupt:
                    logging.warning('terminated by user')
                    print('')
                    print('parent received ctrl-c')
                    break

                except Exception as _err:
                    import traceback

                    logging.error('Error (%s): %s' % (_pos, traceback.format_exc()))
                    logging.error('Error (%s): %s' % (_pos, str(_err)))

                    continue

            _pos += 1

        return _rs

    def create_lock(self):
        return multiprocessing.Lock()


