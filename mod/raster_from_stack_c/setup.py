from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("raster_from_stack_c", ["raster_from_stack.pyx"])]

setup(
	name = "raster_from_stack enhanced with Cython",
	cmdclass = {"build_ext": build_ext},
	ext_modules = ext_modules
)

