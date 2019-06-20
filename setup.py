from setuptools import setup
from setuptools import find_packages

import cocotb_test
version = cocotb_test.__version__

from os import path

def read_file(fname):
    return open(path.join(path.dirname(__file__), fname)).read()

setup(
    name='cocotb-test',
    version=version,
    description='',
    url='',
    license='BSD',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Tomasz Hemperek',
    author_email='hemperek@uni-bonn.de',
    packages=find_packages(),
    install_requires= ['cocotb','pytest'],
    platforms='any',
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
