import os
import os.path as osp
from setuptools import setup, find_packages

with open("sfv/VERSION", "rt") as fin:
    version = fin.read().strip()

setup (
    name="sfv",
    version=version,
    description="SFV: a Python package for visualizing signal flow " \
                "of complex networks in Nezzle.",
    # long_description=long_description,
    # long_description_content_type="text/markdown",
    url="https://github.com/dwgoon/sfv",
    author="Daewon Lee",
    author_email="daewon4you@gmail.com",
    license="BSD 3-Clause License",
    python_requires=">=3.7",
    classifiers=[
        'License :: OSI Approved :: BSD-3-Clause License',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(),
    package_data={
        "": ["VERSION", "*.sif", "*.nzj", "*.json"],
    },
)
