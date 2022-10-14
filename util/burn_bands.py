#!/usr/bin/env python
'''
File: burn_bands.py
Author: Min Feng
Description: burn one band into another one
'''
    
def main(opts): 
    from gio import file_unzip
    from gio import geo_raster as ge
    from gio import band_op as op
    from gio import file_mag
    
    if opts.transparency:
        _out = op.burn_transparency(ge.open(opts.input).get_band().cache(), opts.color_input, opts.refer, opts.transparency[0], opts.transparency[1])
    else:
        _out = op.burn_band(ge.open(opts.input).get_band().cache(), opts.color_input, opts.refer, opts.color_refer, opts.offset)
        
    with file_unzip.zip() as _zip:
        _zip.save(_out, opts.output)
    
def usage():
    _p = environ_mag.usage(False)
    
    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-ci', '--color-input', dest='color_input')
    
    _p.add_argument('-r', '--refer', dest='refer', required=True)
    _p.add_argument('-cr', '--color-refer', dest='color_refer')
    _p.add_argument('-t', '--transparency', dest='transparency', type=float, nargs=2)
    
    _p.add_argument('-s', '--offset', dest='offset', type=int, default=250)
    _p.add_argument('-o', '--output', dest='output', required=True)
    
    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())]) 