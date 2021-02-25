from setuptools import setup
from setuptools import find_packages
import os
import cocotb_test

version = cocotb_test.__version__


def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="cocotb-test",
    version=version,
    description="",
    url="",
    license="BSD",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Tomasz Hemperek",
    author_email="hemperek@uni-bonn.de",
    packages=find_packages(),
    install_requires=["cocotb>=1.5", "pytest"],
    entry_points={
        "console_scripts": [
            "cocotb=cocotb_test.cli:config",
            "cocotb-run=cocotb_test.cli:run",
            "cocotb-clean=cocotb_test.cli:clean",
        ],
        "pytest11": ["pytest-cocotb = cocotb_test.plugin"],
    },
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
