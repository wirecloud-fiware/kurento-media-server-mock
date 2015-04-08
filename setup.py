import sys

from distutils.core import setup

if sys.version_info.major > 2:
    sys.stderr.write("ERROR: You need python2 to execute this!")
    exit(1)


version = 'pa-0.0.1-mn'
description = 'Kurento Media Server JSON-RPC Mock'
long_description = description

classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Operating System :: POSIX',
    'Programming Language :: Python :: 2.7',
    'Topic :: Internet :: WWW/HTTP'
]

setup(name='kms-mock',
      version=version,
      description=description,
      long_description=long_description,
      author='Miguel Garcia Lafuente [Rock Neurotiko]',
      author_email='mgarcia@conwet.com',
      url='http://www.github.com/',
      platforms=['POSIX'],
      py_modules=[''],
      packages=['kmsmock'],
      scripts=['kmsmock/kms-mock.py'],
      classifiers=classifiers,
)
