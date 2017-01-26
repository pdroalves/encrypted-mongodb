from distutils.core import setup, Extension
import numpy
import os

os.environ["CC"] = "clang"

# ore = Extension('LewiWuORE',
#                 libraries=['crypto', 'ssl', 'gmp'],
#                 include_dirs=['/usr/local/include', '../'],
#                 library_dirs=['/usr/local/lib', '../'],
#                 sources=['ore_module.c', "../crypto.c", "../ore.c"],
#                 define_macros=[('NPY_NO_DEPRECATED_API',
#                                 'NPY_1_7_API_VERSION')],
#                 extra_link_args=["-I", "-l", "-g", "-lssl", "-lcrypto"],
#                 extra_compile_args=["-O3", "-Wall", "-march=native"])

oreblk = Extension('LewiWuOREBlk',
                    libraries = ['crypto','ssl', 'gmp'],
                    include_dirs = ['/usr/local/include','../'],
                    library_dirs = ['/usr/local/lib','../'],
                    sources = ['ore_blk_module.c',
                                        "../crypto.c",
                                        "../ore_blk.c",
                                        "../ore.c"],
                    define_macros = [('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
                    extra_link_args=["-I",
                                                    "-l",
                                                    "-g",
                                                    "-lssl","-lcrypto"],
                extra_compile_args=[
                                    "-O3", "-Wall","-march=native"])

oreblk_leftright = Extension('LewiWuOREBlkLF',
                    libraries = ['crypto','ssl', 'gmp'],
                    include_dirs = ['/usr/local/include','../'],
                    library_dirs = ['/usr/local/lib','../'],
                    sources = ['ore_blk_leftright_module.c',
                                        "../crypto.c",
                                        "../ore_blk_leftright.c",
                                        "../ore.c"],
                    define_macros = [('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
                    extra_link_args=["-I",
                                                    "-l",
                                                    "-g",
                                                    "-lssl","-lcrypto"],
                extra_compile_args=[
                                    "-O3", "-Wall","-march=native"])

# setup(name='LewiWuORE',
#       version='1.0',
#       description='This package provides the ORE implementation from Lewi-Wu \
#                    proposal',
#       author='Abe Wiersma',
#       author_email='abe.wiersma@os3.nl',
#       ext_modules=[ore])

setup (name = 'LewiWuOREBlk',
             version = '1.0',
             description = 'This package provides a OREBLK implementation from Lewi-Wu proposal',
             author = 'Pedro Alves',
             author_email = 'pedro.alves@ic.unicamp.br',
             ext_modules = [oreblk])


setup (name = 'LewiWuOREBlkLF',
             version = '1.0',
             description = 'This package provides a OREBLK implementation from Lewi-Wu proposal without the remark 3.1.',
             author = 'Pedro Alves',
             author_email = 'pedro.alves@ic.unicamp.br',
             ext_modules = [oreblk_leftright])
