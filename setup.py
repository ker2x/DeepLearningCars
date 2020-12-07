from setuptools import setup
from Cython.Build import cythonize

# python setup.py build_ext --inplace --force

setup(
    ext_modules = cythonize(["fvector.pyx", "car.pyx", "primitives.pyx", "game.pyx"],
                            annotate=True,
                            compiler_directives={'language_level':3, 'profile': True})
)