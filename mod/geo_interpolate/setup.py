from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("geo_interpolate", ["geo_interpolate.pyx"])]

setup(
	 name = "geo_interpolate",
	 cmdclass = {"build_ext": build_ext},
	 ext_modules = ext_modules
)
