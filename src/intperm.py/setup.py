# -*- coding: utf-8 -*-
"""A simple permutation for arbitrary size integers."""
from setuptools import find_packages, setup


with open('README.rst') as README:
    LONG_DESCRIPTION = README.read()

setup(
    name='intperm',
    version='1.1.1',
    url='https://github.com/attilaolah/intperm.py',
    license='Public Domain',
    author='Attila Oláh',
    author_email='attilaolah@gmail.com',
    description='Pseudo-random permutation of arbitrary size integers.',
    long_description=LONG_DESCRIPTION,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
    ],
    tests_require=[
        'nose',
    ],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=False,
    test_suite='nose.collector',
    zip_safe=True,
)
