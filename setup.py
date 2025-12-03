from setuptools import setup, find_packages
import os

# Read version from cocotb_test/__init__.py without importing the package
version = {}
with open(os.path.join(os.path.dirname(__file__), "cocotb_test", "__init__.py"), "r") as f:
    exec(f.read(), version)

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="cocotb-test",
    version=version["__version__"],
    description="",
    url="",
    license="BSD",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Tomasz Hemperek",
    author_email="hemperek@uni-bonn.de",
    packages=find_packages(include=["cocotb_test", "cocotb_test.*"]),
    include_package_data = True,
    python_requires=">=3.7",
    install_requires=[
        "cocotb>=1.5",
        "pytest",
        "find_libpython",
        "packaging",
    ],
    entry_points={
        "console_scripts": [
            "cocotb-test=cocotb_test.cli:config",
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
        "Framework :: cocotb",
    ],
)
