import logging
from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def walk_files(d):
    fs = []
    for root, _, files in os.walk(d):
        for file in files:
            if file.startswith("."):
                continue
            fs.append((root, file))
    return fs

# Collect Cython extensions
extensions = []
for root, file in walk_files("mod"):
    if not file.endswith(".pyx"):
        continue
    name, _ = os.path.splitext(file)
    if name.endswith("_c"):
        name = name[:-2]
    module_name = f"gio.{name}"
    file_path = os.path.join(root, file)
    logger.debug(f"Found Cython file: {file_path}, module: {module_name}")
    extensions.append(
        Extension(
            module_name,
            sources=[file_path],
            include_dirs=[numpy.get_include()],
            define_macros=[("NPY_NO_DEPRECATED_API", None)],
        )
    )

# Log extensions
logger.debug(f"Registered {len(extensions)} Cython extensions: {[ext.name for ext in extensions]}")

# Collect scripts
scripts = [os.path.join(root, file) for root, file in walk_files("util") if file.endswith(".py")]
logger.debug(f"Registered {len(scripts)} scripts: {[os.path.basename(s) for s in scripts]}")

setup(
    ext_modules=cythonize(
        extensions,
        # compiler_directives={'language_level': '3', 'boundscheck': False, 'wraparound': False},
        # annotate=True,
        build_dir="build/cython",
    ),
    scripts=scripts,
)
