'''
File: metadata.py
Author: Min Feng
Version: 0.1
Create: 2015-07-28 18:30:01
Description:
'''

class metadata(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, idx):
        from gio import config
        if config.cfg.has_option('conf', 'debug') and config.cfg.getboolean('conf', 'debug'):
            import sys
            sys.stdout.write('[%s].' % idx)

        if idx not in self:
            self.__setitem__(idx, metadata())

        return super().__getitem__(idx)

    def __setitem__(self, idx, val):
        from gio import config
        if config.getboolean('conf', 'debug'):
            print('[%s] = %s' % (idx, val))

        super().__setitem__(idx, val)

    def __setattr__(self, name, val):
        return self.__setitem__(name, val)

    def __getattr__(self, name):
        return self.__getitem__(name)

    def _str(self, lev):
        _ls = []
        for _k, _v in list(self.items()):
            if isinstance(_v, metadata):
                _ls.append('%s[%s]' % ('  ' * lev, _k))
                _ls.extend(_v._str(lev+1))
            else:
                _ls.append('%s%s=%s' % ('  ' * lev, _k, _v))

        return _ls

    def save(self, f_out):
        import json
        from gio import file_unzip
        with file_unzip.zip() as _zip:
            _zip.save(json.dumps(self, indent=4, ensure_ascii=False), f_out)

    def save_txt(self, f_out):
        '''save to a customized format'''
        _ls = self._str(0)
        
        from gio import file_unzip
        with file_unzip.zip() as _zip:
            _zip.save('\n'.join(_ls), f_out)

    def __str__(self):
        return '\n'.join(self._str(0))

class metadata_v0(object):

    def __init__(self, meta=None):
        import collections
        self._meta = collections.OrderedDict() if not meta else meta

    def __getitem__(self, idx):
        from gio import config
        if config.cfg.has_option('conf', 'debug') and config.cfg.getboolean('conf', 'debug'):
            import sys
            sys.stdout.write('[%s].' % idx)

        if idx not in self._meta:
            self._meta[idx] = metadata()

        return self._meta[idx]

    def __setitem__(self, idx, val):
        from gio import config
        if config.cfg.has_option('conf', 'debug') and config.cfg.getboolean('conf', 'debug'):
            print('[%s] = %s' % (idx, val))

        self._meta[idx] = val

    def __setattr__(self, name, val):
        if name.startswith('_'):
            return super(metadata, self).__setattr__(name, val)
        return self.__setitem__(name, val)

    def __getattr__(self, name):
        if name.startswith('_'):
            return super(metadata, self).__getattr__(name)
        return self.__getitem__(name)

    def _str(self, lev):
        if self._meta == None:
            return []

        assert isinstance(self._meta, dict)

        _ls = []
        for _k, _v in list(self._meta.items()):
            if isinstance(_v, metadata):
                _ls.append('%s[%s]' % ('  ' * lev, _k))
                _ls.extend(_v._str(lev+1))
            else:
                _ls.append('%s%s=%s' % ('  ' * lev, _k, _v))

        return _ls

    def save(self, f_out):
        import json
        from gio import file_unzip
        with file_unzip.zip() as _zip:
            _zip.save(json.dumps(self, indent=4, ensure_ascii=False, default=_convert), f_out)

    def save_txt(self, f_out):
        '''save to a customized format'''
        _ls = self._str(0)
        
        from gio import file_unzip
        with file_unzip.zip() as _zip:
            _zip.save('\n'.join(_ls), f_out)

    def __str__(self):
        return '\n'.join(self._str(0))

def load(f):
    from gio import file_mag
    with open(file_mag.get(f).get()) as _fi:
        import json
        # import collections
        # _obj = json.load(_fi, object_hook=_to_obj, object_pairs_hook=collections.OrderedDict)
        _obj = json.load(_fi, object_hook=_to_obj, object_pairs_hook=metadata)
        return _obj

def _to_obj_ex(v):
    _ds = {}

    for _k, _v in v:
        _ds[_k.strip()] = _v.strip if _v is str else _v

    return metadata(_ds)

def _to_obj(obj):
    if isinstance(obj, dict):
        return metadata(obj)

    return obj

def _convert(obj):
    if isinstance(obj, metadata):
        return obj._meta
    return obj

def _object(obj):
    if isinstance(obj, dict):
        return metadata(obj)
    return obj

def main(opts):
    _m = metadata()
    _m['name'] = 'mfeng'
    print(_m['test1'])
    _m['test1']['test2'] = 23
    _m['test1']['test3'] = 22
    _m['test1']['test4'] = 'test'
    _m['test1']['test5']['test2'] = 'test'
    _m['test1']['test5']['test3'] = {'t1': 23, 't2': 'www', 't3': {'z1': 22, 'z2': [23]}}
    _m.test2.test3 = 'tttt'

    _m.save('test1.txt')

    _m = load('test1.txt')
    print(_m.test1.test4)
    print(_m['test1']['test4'])
    print(_m)

def usage():
    _p = environ_mag.usage(False)
    
    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())]) 