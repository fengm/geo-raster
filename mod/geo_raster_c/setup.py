from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("geo_raster_c", ["geo_raster_c.pyx"])]

setup(
	name = "GeoRaster enhanced with Cython",
	cmdclass = {"build_ext": build_ext},
	ext_modules = ext_modules
)

