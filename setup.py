from setuptools import setup
from setuptools import find_packages
from setuptools import Extension
import os
import cocotb_test

version = cocotb_test.__version__


def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


from setuptools.command.install import install
from setuptools.command.develop import develop


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)

        lib_dir = os.path.join(self.install_lib, "cocotb_test", "libs")
        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        from cocotb_test.build_libs import build_libs

        build_libs(build_dir=lib_dir)


class PostDevelopCommand(develop):
    """Post-installation for develop mode."""

    def run(self):
        develop.run(self)

        lib_dir = os.path.join(os.path.dirname(cocotb_test.__file__), "libs")
        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        from cocotb_test.build_libs import build_libs

        build_libs(build_dir=lib_dir)


# force platform specyfic wheel  (root_is_pure)
try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            self.root_is_pure = False


except ImportError:
    bdist_wheel = None

setup(
    name="cocotb-test",
    cmdclass={"install": PostInstallCommand, "develop": PostDevelopCommand, "bdist_wheel": bdist_wheel},
    version=version,
    description="",
    url="",
    license="BSD",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Tomasz Hemperek",
    author_email="hemperek@uni-bonn.de",
    packages=find_packages(),
    setup_requires=["cocotb"],
    install_requires=["cocotb", "pytest"],
    entry_points={
        "console_scripts": ["cocotb=cocotb_test.cli:config", "cocotb-run=cocotb_test.cli:run", "cocotb-clean=cocotb_test.cli:clean"],
        "pytest11": ["pytest-cocotb = cocotb_test.plugin"],
    },
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
