'''
File: band_op.py
Author: Min Feng
Description: operate bands
'''

import logging

def burn_band(bnd, clr_bnd, ref, clr_ref, offset=250, alpha_only=False):
    '''burn another band into the source band to create RGB image'''
    
    from gio import geo_raster as ge
    from gio import geo_raster_ex as gx
    import numpy as np
    
    if isinstance(ref, ge.geo_band_cache):
        _ref = ref.read_block(bnd)
    else:
        _ref = gx.read_block(ref, bnd)
        
    if bnd is None or _ref is None:
        return None
        
    _bnd = bnd if len(bnd.data.shape) > 2 else bnd.colorize_rgba(clr_bnd)
    if _ref.color_table is None and clr_ref is None and _ref.pixel_type == ge.pixel_type():
        _r = np.zeros((4, _bnd.height, _bnd.width), dtype=np.uint8)
        for _b in range(3):
            _r[_b, :, :] = _ref.data
            
        _r[3, :, :] = 255
        if _ref.nodata is not None:
            _r[3, :, :][_ref.data == _ref.nodata] = 0
            
        _ref = _ref.from_grid(_r)
    else:
        _ref = _ref.colorize_rgba(clr_ref) 
    
    _d = np.zeros((4, _bnd.height, _bnd.width), dtype=np.int16)
    if not alpha_only:
        for _n in range(3):
            _o = _bnd.data[_n, :, :].astype(np.int16)
            _x = _ref.data[_n, :, :]
            
            _o += _x
            _o -= offset
            
            _o[_o < 0] = 0
            _o[_o > 255] = 255
            
            _d[_n, :, :] = _o.astype(np.uint8)
        
    _a = _bnd.data[3, :, :]
    _a[_ref.data[3, :, :] == 0] = 0
    _d[3, :, :] = _a
    
    _out = _bnd.from_grid(_d.astype(np.uint8))
    return _out
    
def burn_transparency(bnd, clr_bnd, ref, v_min, v_max):
    '''burn another band into the source band as transparency to create RGB image'''
    
    from gio import geo_raster as ge
    from gio import geo_raster_ex as gx
    import numpy as np
    
    if isinstance(ref, ge.geo_band_cache):
        _ref = ref.read_block(bnd)
    else:
        _ref = gx.read_block(ref, bnd)
        
    if bnd is None or _ref is None:
        return None
        
    _bnd = bnd if len(bnd.data.shape) > 2 else bnd.colorize_rgba(clr_bnd)
    
    _d = (_ref.data - v_min) * 255 / (v_max - v_min)
    _d[_d < 0] = 0
    _d[_d > 255] = 255
    
    if _ref.nodata is not None:
        _d[_ref.data == _ref.nodata] = 0
    
    _bnd.data[3, :, :] = _d.astype(np.uint8)
    return _bnd
    