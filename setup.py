from setuptools import setup
try:
    from pip.req import parse_requirements
except ModuleNotFoundError:
    from pip._internal.req import parse_requirements

import sys
if sys.version_info<(3,3):
    print("This python version is not supported:")
    print(sys.version)
    print("agutil requires python 3.3 or greater")
    sys.exit(1)

long_desc = "A collection of python utilities"
version = None

import re
try:
    reader = open("README.rst", mode='r')
    long_desc = reader.read()
    version = re.search(r'\*\*Version:\*\* ([0-9\.a-zA-Z]*)', long_desc).group(1)
    reader.close()
except OSError:
    pass

if not version:
    reader = open("README.md", mode='r')
    long_desc = reader.read()
    version = re.search(r'__Version:__ ([0-9\.a-zA-Z]*)', long_desc).group(1)
    reader.close()

setup(
    name="agutil",
    version=version,
    packages=[
        "agutil",
        "agutil.bio",
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
            "maf2bed = agutil.bio.maf2bed:main",
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

        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ],

    author = "Aaron Graubert",
    author_email = "captianjroot@live.com",
    description = "A collection of python utilities",
    long_description = long_desc,
    license = "MIT",
    keywords = "range progress bar loading encryption decryption RSA AES io sockets utilities",
    url = "https://github.com/agraubert/agutil",   #
)
