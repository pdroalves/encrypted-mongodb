from distutils.core import setup, Extension
import numpy

module1 = Extension('BFIBE',
					libraries = ['relic'],
					include_dirs = ['/usr/local/include/relic',numpy.get_include()],
					library_dirs = ['/usr/local/lib'],
          sources = ['bfibemodule.c'],
          define_macros = [('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
          extra_link_args=["-I",
				"/usr/include/relic",
				"-l",
				"relic",
        "-g"],
        extra_compile_args=[
                  "--std=c99"])

setup (name = 'BFIBE',
       version = '1.0',
       description = 'This package provides a BF-IBE implementation from RELIC',
       author = 'Pedro Alves',
       author_email = 'pedro.alves@ic.unicamp.br',
       ext_modules = [module1])
