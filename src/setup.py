from setuptools import setup

setup(name='secmongo',
      version='0.1',
      description='Secure end->end mongo implementation',
      url='https://github.com/maxgrim/encrypted-mongodb/tree/os3',
      author='Max Grim & Abe Wiersma',
      author_email='max.grim@os3.nl',
      license='MIT',
      packages=['secmongo', 'secmongo/crypto', 'secmongo/index', 'secmongo/scripts'],
      package_data={'secmongo/crypto': ['*'], 'secmongo/index': ['*'],
                    'secmongo/scripts': ['*.js']},
      zip_safe=False)
