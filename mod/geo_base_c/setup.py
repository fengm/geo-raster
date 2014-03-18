from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("geo_base_c", ["geo_base_c.pyx"])]

setup(
	name = "GeoBase enhanced with Cython",
	cmdclass = {"build_ext": build_ext},
	ext_modules = ext_modules
)

