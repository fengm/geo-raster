from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("aggregate_band", ["aggregate_band.pyx"])]

setup(
	 name = "aggregate_band",
	 cmdclass = {"build_ext": build_ext},
	 ext_modules = ext_modules
)
