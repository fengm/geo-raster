from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("lc_agg_module", ["lc_agg_module.pyx"])]

setup(
	name = "Average LC pixels",
	cmdclass = {"build_ext": build_ext},
	ext_modules = ext_modules
)

