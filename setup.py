from setuptools import setup

import sys
if sys.version_info<(3,3):
    print("This python version is not supported:")
    print(sys.version)
    print("agutil requires python 3.0 or greater")
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
    raise ValueError("Unable to parse version number from README.rst")

setup(
    name="agutil",
    version=version,
    packages=[
        "agutil",
        "agutil.bio",
        "agutil.src",
        "agutil.io",
        "agutil.io.src"
    ],
    entry_points={
        "console_scripts":[
            "maf2bed = agutil.bio.maf2bed:main",
            "tsvmanip = agutil.bio.tsvmanip:main"
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Utilities',

        'License :: OSI Approved :: MIT License',

        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
    ],

    author = "Aaron Graubert",
    author_email = "captianjroot@live.com",
    description = "A collection of python utilities",
    long_description = long_desc,
    license = "MIT",
    keywords = "range progress bar loading utilities",
    url = "https://github.com/agraubert/agutil",   #
)
