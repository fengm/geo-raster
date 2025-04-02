'''
File: metadata.py
Author: Min Feng
Version: 0.1
Create: 2015-07-28 18:30:01
Description:
'''

def _debug():
    from gio import config
    return config.has_option('conf', 'debug') and config.getboolean('conf', 'debug')

class metadata(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, idx):
        if _debug():
            import sys
            sys.stdout.write('[%s].' % idx)

        if idx not in self:
            self.__setitem__(idx, metadata())

        return super().__getitem__(idx)

    def __setitem__(self, idx, val):
        if isinstance(idx, str) and idx.startswith('_ipython'):
            return None
            
        from gio import config
        if _debug():
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

    def getint(self, k, val=None):
        _v = self.get(k, val)
        if _v is None:
            return _v
        return int(_v)

    def getfloat(self, k, val=None):
        _v = self.get(k, val)
        if _v is None:
            return _v
        return float(_v)

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

    def copy(self):
        _as = {}
        for _k, _v in list(self.items()):
            if isinstance(_v, metadata):
                _as[_k] = _v.copy()
            else:
                _as[_k] = _v
        return metadata(_as)

def _to_obj(obj):
    if isinstance(obj, dict):
        return metadata(obj)

    return obj

def load(f):
    from gio import file_mag
    import json

    return json.loads(file_mag.get(f).read().decode('utf-8'), object_hook=_to_obj, object_pairs_hook=metadata)
