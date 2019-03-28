from setuptools import setup
try:
    from pip.req import parse_requirements
except ImportError:
    from pip._internal.req import parse_requirements

import sys
if sys.version_info == (3.3):
    import warnings
    warnings.warn(
        "Warning: Python 3.3 is no longer officially supported by agutil"
    )
elif sys.version_info<(3,4):
    print("This python version is not supported:")
    print(sys.version)
    print("agutil requires python 3.4 or greater")
    sys.exit(1)

long_desc = "A collection of python utilities"

import re, os
if os.path.isfile('README.rst'):
    reader = open("README.rst", mode='r')
else:
    reader = open("README.md", mode='r')
long_desc = reader.read()
reader.close()

from agutil import __version__ as version

setup(
    name="agutil",
    version=version,
    packages=[
        "agutil",
        "agutil.io",
        "agutil.io.src",
        "agutil.parallel",
        "agutil.parallel.src",
        "agutil.security",
        "agutil.security.src",
        "agutil.src",
    ],
    entry_points={
        "console_scripts":[
            "agutil-secure = agutil.security.console:main"
        ]
    },
    install_requires=[
        str(package.req) for package in parse_requirements(
            'requirements.txt',
            session=''
        )
    ],
    tests_require=[
        str(package.req) for package in parse_requirements(
            'tests/requirements.txt',
            session=''
        )
    ],
    test_suite='tests',
    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Security :: Cryptography',
        'Topic :: Utilities',

        'License :: OSI Approved :: MIT License',

        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only"
    ],

    author = "Aaron Graubert",
    author_email = "captianjroot@live.com",
    description = "A collection of python utilities",
    long_description = long_desc,
    license = "MIT",
    keywords = "range progress bar loading encryption decryption RSA AES io sockets utilities",
    url = "https://github.com/agraubert/agutil",   #
)
