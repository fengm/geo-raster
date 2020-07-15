
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("geo_base_c", ["geo_base_c.pyx"],
		#extra_compile_args=["-O3", "-ffast-math","-funroll-loops"],
		define_macros=[("NPY_NO_DEPRECATED_API", None)])]

setup(
	name = "GeoBase enhanced with Cython",
	cmdclass = {"build_ext": build_ext},
	ext_modules = ext_modules
)

