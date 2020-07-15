
'''
File: progress_percentage.py
Author: Min Feng
Version: 0.1
Create: 2012-03-08 14:41:34
Description: Show progress in percentage
'''
'''
Version: 0.2
Date: 2012-06-25 14:41:27
Note: Option for showing the progress bar
'''
import datetime, logging, sys

class progress:

    def __init__(self, size, title=None, step=100, txt_format='%(p)3d%%', bar=False, perc_step=None):
        self.pos = 0
        self.cur = -1
        self.size = size
        self.step = step
        self.txt_format = txt_format
        self.time_s = datetime.datetime.now()

        from . import config
        _debug = config.getboolean('conf', 'debug')
        
        _step = 1 if _debug else config.getfloat('conf', 'progress_step', 10)
        if perc_step is not None:
            _step = perc_step

        self.min_perc_step = _step

        self.title = title
        self.bar = bar
        self.text = ''
        self.show = config.getboolean('conf', 'show_progress', _debug)

        logging.debug('+ start process :' + title if title != None \
                else '<no name>')
        if title != None:
            print('>', title)

    def _print(self, txt):
        if not self.show:
            return

        print('\r', txt, end=' ')
        if len(self.text) > len(txt):
            print(' ' * (len(self.text) - len(txt)), end=' ')
        sys.stdout.flush()

        self.text = txt

    def print_prog(self, pos):
        _pos = pos if pos <= 100 else 100

        _out = []
        if self.bar:
            _len_l = _pos / 2
            if _len_l == 0:
                _len_l = 1
            _len_r = 100 / 2 - _len_l

            _txt = ''
            _txt += '=' * (_len_l - 1)
            _txt += '>'
            _txt += '-' * _len_r
            _out.append(_txt)

        _out.append(self.txt_format % {'p': _pos})
        _out.append('(%s)' % (datetime.datetime.now() - self.time_s))

        _txt = ' '.join(_out)
        if pos == 100 or self.min_perc_step > 0:
            logging.info(_txt)

        self._print(_txt)
        
    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self, step=1, count=False, message=None):
        self.cur += step

        if count:
            if self.show:
                _out = ['']
                _out.append('%s/%s: %s' % (self.cur, self.size, message if message else ''))
                _out.append('(%s)' % (datetime.datetime.now() - self.time_s))

                self._print(' '.join(_out))
        else:
            _pos = self.cur * self.step // self.size

            if _pos - self.pos >= self.min_perc_step:
                self.pos = _pos
                self.print_prog(self.pos * 100 / self.step)

    def done(self, format_end='\r%(p)3d%% | duration: %(time_duration)s'):
        self.print_prog(100)
        if self.show:
            print('')

        self.time_e = datetime.datetime.now()
        _d = self.time_e - self.time_s

        logging.debug('- end process ' + format_end % {'p': 100, 'time_duration': _d, \
                'time_start': self.time_s, 'time_end': self.time_e})

