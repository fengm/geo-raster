#!/usr/bin/env python
'''
File: extract_tile_records.py
Author: Min Feng
Description: the script extract the tile info from a CSV or shapefile and save to a txt file
'''

def main(opts):
    import logging
    from gio import file_mag
    
    _f_inp = file_mag.get(opts.input).get()
    if not _f_inp or os.path.exists() == False:
        raise Exception('failed to find the input file %s' % opts.input)
    
    _ts = []
    if opts.input.endswith('.csv'):
        from gio import csv_util
        for _r in csv_util.open(_f_inp):
            _ts.append(_r.get(opts.column))
            
    elif opts.input.endswith('.shp'):
        from gio import geo_base as gb
        for _g, _r in gb.load_shp(_f_inp):
            _ts.append(_r.get(opts.column))
    else:
        raise Exception('failed to recognize the file %s' % ots.input)
        
    _f_out = opts.output if opts.output else opts.input[:-4] + '.txt'
    
    logging.info('save %s records to %s' % (len(_ts), _f_out))
    print('save %s records to %s' % (len(_ts), _f_out))
    
    from gio import file_unzip
    file_unzip.save('\n'.join(_ts), _f_out)

def usage():
    _p = environ_mag.usage(False)

    _p.add_argument('-i', '--input', dest='input', required=True)
    _p.add_argument('-c', '--column', dest='column', default='TILE')
    _p.add_argument('-o', '--output', dest='output')
    
    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())]) 
    