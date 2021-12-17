from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("agg_band", ["agg_band.pyx"])]

setup(
	 name = "agg_band",
	 cmdclass = {"build_ext": build_ext},
	 ext_modules = ext_modules
)
