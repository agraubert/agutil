from setuptools import setup

import sys
if sys.version_info[0]<3:
    print("This python version is not supported:")
    print(sys.version)
    print("agutil requires python 3.0 or greater")
    sys.exit(1)

setup(
    name="agutil",
    version="0.2.0a",
    packages=["agutil", "agutil.bio", "agutil.src"],
    entry_points={
        "console_scripts":[
            "maf2bed = agutil.bio.maf2bed:main",
            "tsvmanip = agutil.bio.tsvmanip:main"
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Utilities',

        'License :: OSI Approved :: MIT License',

        "Programming Language :: Python :: 3"
    ],

    author = "Aaron Graubert",
    author_email = "captianjroot@live.com",
    description = "A collection of python utilities",
    license = "MIT",
    keywords = "range progress bar loading utilities",
    url = "https://github.com/agraubert/agutil",   #
)
