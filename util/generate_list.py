#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
File: generate_list.py
Author: Min Feng
Version: 0.1
Create: 2015-03-10 11:44:38
Description: generate list of files in a folder
'''

def format_path(f):
    import re

    _m = re.match('/a/[^/]+(/.+)', f)
    if _m:
        return _m.group(1)

    return f

def output_list(f, ls):
	from gio import file_unzip
	import os
	
	with file_unzip.file_unzip() as _zip:
		_d_out = _zip.generate_file()
		os.makedirs(_d_out)
		
		_f_out = os.path.join(_d_out, os.path.basename(f))
		
		with open(_f_out, 'w') as _fo:
		    _fo.write('\n'.join(ls))
		    
		_d_ttt = os.path.dirname(f)
		if not _d_ttt:
			_d_ttt = os.path.dirname(os.path.abspath(f))
			
		file_unzip.compress_folder(_d_out, _d_ttt, [])

def main(opts):
    import os
    import re
    import logging
    from gio import file_mag

    _fs = []
    for _dd in opts.input:
        if not _dd:
            continue
        
        _df = file_mag.get((lambda x: x if x.startswith('s3://') else format_path(os.path.abspath(x)))(_dd))
        # if _df.exists() == False:
        #     logging.warning('skip %s' % _dd)
        #     continue
        
        for _f in _df.list(recursive=True):
            if not opts.pattern or re.search(opts.pattern, str(_f)):
                if isinstance(_f, file_mag.file_mag):
                    if os.path.getsize(_f.get()) <= 0:
                        logging.warning('skip zero size file: %s' % _f)
                        continue
                    
                _fs.append(str(_f))

    if len(_fs) == 0:
        print(' * no file was found')
        return
    
    if not opts.output:
        for _l in _fs:
            print(_l)
        return
        

    print('found', len(_fs), 'files')
    output_list(opts.output, _fs + ['\n'])

    if not opts.extent:
        return
    
    print('generate raster extent')
    from gio import run_commands
    
    _tsk = '-in %s -ip %s -ts %s %s -tw %s -to %s' % ( \
            opts.instance_num, opts.instance_pos, opts.task_num, \
                    '-se' if opts.skip_error else '', opts.time_wait, opts.task_order)

    if opts.extent_type == 'wrs2':
        print('generate WRS2 raster extent')
        
        _cmd = 'retrieve_landsat_tiles.py -i %s' % opts.output
        run_commands.run(_cmd)
        
        _cmd = 'landsat_tiles_csv2shp.py -i %s' % opts.output[:-3] + 'csv'
        run_commands.run(_cmd)
        return

    _cmd = 'raster_extent2shp.py -i %s ' % opts.output

    if opts.extent_type == 'gcs':
        print('generate GCS raster extent')
        run_commands.run(_cmd + ' -p 4326')
        return

    if opts.extent_type == 'sin':
        print('generate sinusoidal raster extent')
        run_commands.run(_cmd + ' -p sin')
        return

    run_commands.run(_cmd + _tsk)

def usage():
    _p = environ_mag.usage(True)

    _p.add_argument('-i', '--input', dest='input', nargs='+', required=True)
    _p.add_argument('-z', '--skip-zero-file', dest='skip_zero_file', action='store_true')
    _p.add_argument('-o', '--output', dest='output')
    _p.add_argument('-p', '--pattern', dest='pattern')

    _p.add_argument('-e', '--extent', dest='extent', action='store_true', \
            help='run raster_extent2shp after the list is generated')

    _p.add_argument('-t', '--extent-type', dest='extent_type')

    return _p

if __name__ == '__main__':
    from gio import environ_mag
    environ_mag.init_path()
    environ_mag.run(main, [environ_mag.config(usage())])