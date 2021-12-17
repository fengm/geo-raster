#!/usr/bin/env python
# encoding: utf-8

'''
File: convert_to_geotiff.py
Author: Min Feng
Version: 0.1
Create: 2016-09-01 11:33:00
Description: convert images to GeoTIFF format
'''

def convert_file(f_img, f_clr, d_out):
    import logging
    from gio import file_unzip
    from gio import file_mag
    
    with file_unzip.zip() as _zip:
        import os

        from gio import geo_raster as ge
        _bnd = ge.open(f_img).get_band().cache()

        _clr = _bnd.color_table
        if f_clr:
            # from gio import color_table
            # _clr = color_table.color_table(f_clr).ogr_color_table()
            _clr = ge.load_colortable(f_clr)
            _bnd.color_table = _clr
        
        _f_out = d_out
        if os.path.isdir(_f_out) or _f_out.endswith(os.path.sep):
            _f_out = os.path.join(_f_out, os.path.splitext(os.path.basename(f_img))[0] + '.tif')
            
        logging.info('output to %s' % _f_out)
        _zip.save(_bnd, _f_out)
        
def main(opts):
    _ls = [opts.input] if not opts.input.endswith('.txt') else open(opts.input).read().strip().splitlines()

    from gio import multi_task
    _ps = [(_l, opts.color, opts.output) for _l in multi_task.load(_ls, opts)]

    multi_task.run(convert_file, _ps, opts)
    print('')

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-c', '--color', dest='color')
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])
