from setuptools import setup

setup(name='secmongo',
      version='0.1',
      description='Secure end->end mongo implementation',
      url='https://github.com/pdroalves/encrypted-mongodb',
      author='Pedro Alves & Diego Aranha & Max Grim & Abe Wiersma',
      author_email='pedro.alves@ic.unicamp.br',
      license='GPLv3',
      packages=['secmongo', 'secmongo/crypto', 'secmongo/index', 'secmongo/scripts'],
      package_data={'secmongo/crypto': ['*'], 'secmongo/index': ['*'],
                    'secmongo/scripts': ['*.js']},
      zip_safe=False)
