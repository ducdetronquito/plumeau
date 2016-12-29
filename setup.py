from distutils.core import setup
from setuptools import find_packages


setup(
    name = 'plume',
    packages = find_packages(exclude=['tests*']),
    version = '0.1',
    description = 'A tiny ORM for SQLite databases.',
    author = 'Guillaume Paulet',
    author_email = 'guillaume.paulet@etu.univ-nantes.fr',
    license='Public Domain',
    url = 'https://github.com/ducdetronquito/plume',
    download_url = 'https://github.com/ducdetronquito/plume/tarball/0.1',
    keywords = ['orm', 'sqlite'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
