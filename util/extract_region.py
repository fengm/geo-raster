'''
File: extract_region.py
Author: Min Feng
Version: 0.1
Create: 2018-01-04 16:53:27
Description:
'''

def main(opts):
    from gio import geo_raster as ge
    from gio import geo_raster_ex as gx

    _clr = None if not opts.color else ge.load_colortable(opts.color)
    _bnd = None

    if opts.input.endswith('.shp'):
        _bnd = gx.geo_band_stack_zip.from_shapefile(opts.input)
    else:
        _bnd = ge.open(opts.input).get_band()

    _mak = ge.open(opts.mask).get_band().cache()
    _bnd = _bnd.read_block(_mak)
    _bnd.data[_mak.data == 0] = _bnd.nodata

    _clr = _clr if _clr else _bnd.color_table

    from gio import file_unzip
    import os
    with file_unzip.file_unzip() as _zip:
        _d_tmp = _zip.generate_file()
        _f_tmp = os.path.join(_d_tmp, os.path.basename(opts.output))

        os.makedirs(_d_tmp)
        _bnd.save(_f_tmp, color_table=_clr, opts=['compress=lzw', 'tiled=yes'])

        file_unzip.compress_folder(_d_tmp, os.path.dirname(os.path.abspath(opts.output)), [])

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-m', '--mask', dest='mask', required=True)
    _p.add_argument('-c', '--color', dest='color')
    _p.add_argument('-o', '--output', dest='output', required=True)

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])

