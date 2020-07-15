
def to_dtype(pixel_type):
	import numpy

	if pixel_type == 1:
		return numpy.uint8
	if pixel_type == 2:
		return numpy.uint16
	if pixel_type == 3:
		return numpy.int16
	if pixel_type == 4:
		return numpy.uint32
	if pixel_type == 5:
		return numpy.int32
	if pixel_type == 6:
		return numpy.float32
	if pixel_type == 7:
		return numpy.float64

	raise Exception('unknown pixel type ' + pixel_type)

def retrieve_raster_file(f_img, dataset_name, f_ref, f_out, d_tmp):
	import geo_raster

	_img = geo_raster.geo_raster.open(f_ref)
	_bnd = _img.get_band()

	_dat = retrieve_raster(f_img, dataset_name, _bnd.band_info(), d_tmp)
	_dat.write(f_out)

def retrieve_raster(f_img, dataset_name, bnd_info, d_tmp):
	import geo_raster_ex

	import file_unzip
	_zip = file_unzip.file_unzip(d_tmp)
	try:
		_stk = geo_raster_ex.geo_band_stack_zip.from_shapefile(f_img,
				dataset_name=dataset_name, file_unzip=_zip)

		_dat = _stk.read_block(bnd_info)
		return _dat

	finally:
		_zip.clean()

