'''
File: band_op.py
Author: Min Feng
Description: operate bands
'''

def burn_band(bnd, clr_bnd, ref, clr_ref, offset=250):
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
        
    _bnd = bnd.colorize_rgba(clr_bnd)
    _ref = _ref.colorize_rgba(clr_ref) 
    
    _d = np.zeros((4, _bnd.height, _bnd.width), dtype=np.int16)
    for _n in range(3):
        _o = _bnd.data[_n, :, :].astype(np.int16)
        _x = _ref.data[_n, :, :]
        
        _o += _x
        _o -= offset
        
        _o[_o < 0] = 0
        _o[_o > 255] = 255
        
        _d[_n, :, :] = _o.astype(np.uint8)
        
    _d[3, :, :] = _bnd.data[3, :, :]
    return _bnd.from_grid(_d)
    
def burn_transparency(bnd, clr_bnd, ref, v_min, v_max, offset=250):
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
        
    _bnd = bnd.colorize_rgba(clr_bnd)
    
    _d = (_ref.data - v_min) * 255 / (v_max - v_min)
    _d[_d < 0] = 0
    _d[_d > 255] = 255
    
    if _ref.nodata is not None:
        _d[_ref.data == _ref.nodata] = 0
    
    _bnd.data[3, :, :] = _d.astype(np.uint8)
    return _bnd
    