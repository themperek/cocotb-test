#!/bin/env python3

import argparse
import os
import sys
import sysconfig
import cocotb
import errno
import distutils
import shutil
import logging

logger = logging.getLogger(__name__)

# import distutils.log
# distutils.log.set_verbosity(-1) # Disable logging in disutils
# distutils.log.set_verbosity(distutils.log.DEBUG) # Set DEBUG level

from setuptools import Extension
from setuptools.dist import Distribution

from xml.etree import cElementTree as ET
import pytest
from distutils.spawn import find_executable

from setuptools.command.build_ext import build_ext as _build_ext

# Needed for Windows to not assume python module (generate interface in def file)
class build_ext(_build_ext):
    def get_export_symbols(self, ext):
        return None


def _rename_safe(target, link_name):
    """Rename or symlink on Mac or copy on Windows."""

    if sys.platform == "darwin":  # On Mac there is an issue with rename? Workaround!
        try:
             os.symlink(target, link_name)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.remove(link_name)
                os.symlink(target, link_name)
            else:
                raise e
        return 

    if os.name == "nt":  # On Windows there is an issue with symlink and rename? !Workaround!
        shutil.copy2(target, link_name)
        return

    try:
        os.rename(target, link_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.rename(target, link_name)
        else:
            raise e


def _build_lib(lib, dist, build_dir):
    """Use setuptools to build `lib` into `build_dir`."""

    dist.ext_modules = [lib]

    _build_ext = build_ext(dist)
    _build_ext.build_lib = build_dir
    _build_ext.build_temp = build_dir

    _build_ext.finalize_options()

    _build_ext.run()
    out_lib = _build_ext.get_outputs()

    lib_name = lib.name
    lib_path = os.path.abspath(out_lib[0])
    dir_name = os.path.dirname(lib_path)
    ext_name = os.path.splitext(lib_path)[1][1:]
    if os.name == "nt":
        ext_name = "dll"

    target = os.path.join(os.path.abspath(dir_name), lib_name + "." + ext_name)
    if target != lib_path:
        _rename_safe(
            lib_path, os.path.join(os.path.abspath(dir_name), lib_name + "." + ext_name)
        )

    return dir_name, ext_name


def build_libs(build_dir="cocotb_build"):
    """Call `_build_lib()` for all necessary libraries.

    Some libraries are built only depending on the SIM environment variable."""

    cfg_vars = distutils.sysconfig.get_config_vars()
    for key, value in cfg_vars.items():
        if type(value) == str:
            cfg_vars[key] = value.replace("-Wstrict-prototypes", "")

    if sys.platform == "darwin":
        cfg_vars["LDSHARED"] = cfg_vars["LDSHARED"].replace("-bundle", "-dynamiclib")

    share_dir = os.path.join(os.path.dirname(cocotb.__file__), "share")
    share_lib_dir = os.path.join(share_dir, "lib")
    # build_dir_abs = os.path.join(os.getcwd(), build_dir)
    build_dir_abs = os.path.abspath(build_dir)

    ext_modules = []

    if os.name == "nt":
        ext_name = "dll"
        python_version = distutils.sysconfig.get_python_version()
        python_version.replace(".", "")
        python_lib = "python" + python_version + ".dll"
        python_lib_link = python_lib.split(".")[0]
    else:
        python_lib = sysconfig.get_config_var("LDLIBRARY")
        python_lib_link = os.path.splitext(python_lib)[0][3:]
        ext_name = "so"

    include_dir = os.path.join(share_dir, "include")

    dist = Distribution()
    dist.parse_config_files()

    def build_libs_common(build_dir_abs):
        libcocotbutils = Extension(
            "libcocotbutils",
            include_dirs=[include_dir],
            sources=[os.path.join(share_lib_dir, "utils", "cocotb_utils.c")],
            extra_link_args=["-Wl,-rpath,$ORIGIN"],
        )

        _build_lib(libcocotbutils, dist, build_dir_abs)

        gpilog_ex_link_args = []
        if sys.platform == "darwin":
            gpilog_ex_link_args = ["-Wl,-rpath," + sysconfig.get_config_var("LIBDIR")]

        libgpilog = Extension(
            "libgpilog",
            include_dirs=[include_dir],
            libraries=[python_lib_link, "pthread", "m", "cocotbutils"],
            library_dirs=[build_dir_abs],
            sources=[os.path.join(share_lib_dir, "gpi_log", "gpi_logging.c")],
            extra_link_args=gpilog_ex_link_args,
        )

        _build_lib(libgpilog, dist, build_dir_abs)

        libcocotb = Extension(
            "libcocotb",
            define_macros=[("PYTHON_SO_LIB", python_lib)],
            include_dirs=[include_dir],
            library_dirs=[build_dir_abs],
            libraries=["gpilog", "cocotbutils"],
            sources=[os.path.join(share_lib_dir, "embed", "gpi_embed.c")],
            extra_link_args=["-Wl,-rpath,$ORIGIN"],
        )

        _build_lib(libcocotb, dist, build_dir_abs)

        libgpi = Extension(
            "libgpi",
            define_macros=[("LIB_EXT", ext_name), ("SINGLETON_HANDLES", "")],
            include_dirs=[include_dir],
            libraries=["cocotbutils", "gpilog", "cocotb", "stdc++"],
            library_dirs=[build_dir_abs],
            sources=[
                os.path.join(share_lib_dir, "gpi", "GpiCbHdl.cpp"),
                os.path.join(share_lib_dir, "gpi", "GpiCommon.cpp"),
            ],
            extra_link_args=["-Wl,-rpath,$ORIGIN"],
        )

        _build_lib(libgpi, dist, build_dir_abs)

        libsim = Extension(
            "simulator",
            include_dirs=[include_dir],
            libraries=["cocotbutils", "gpilog", "gpi"],
            library_dirs=[build_dir_abs],
            sources=[os.path.join(share_lib_dir, "simulator", "simulatormodule.c")],
        )

        _build_lib(libsim, dist, build_dir_abs)

    # VPI common
    libvpi_define_macros = [("VPI_CHECKING", "1")]
    libvpi_include_dirs = [include_dir]
    libvpi_libraries = ["gpi", "gpilog"]
    # libvpi_library_dirs = [build_dir_abs]
    libvpi_sources = [
        os.path.join(share_lib_dir, "vpi", "VpiImpl.cpp"),
        os.path.join(share_lib_dir, "vpi", "VpiCbHdl.cpp"),
    ]
    libvpi_extra_link_args = ["-Wl,-rpath,$ORIGIN"]

    # For Icarus
    icarus_extra_lib = []
    icarus_extra_lib_path = []
    icarus_compile = True
    icarus_build_dir = os.path.join(build_dir_abs, "icarus")
    libvpi_library_dirs = [icarus_build_dir]
    if os.name == "nt":
        iverilog_path = find_executable("iverilog")
        if iverilog_path is None:
            logger.warning(
                "Icarus Verilog executable not found. VPI interface will not be avaliable."
            )
            icarus_compile = False
        else:
            icarus_path = os.path.dirname(os.path.dirname(iverilog_path))
            icarus_extra_lib = ["vpi"]
            icarus_extra_lib_path = [os.path.join(icarus_path, "lib")]

    if icarus_compile:
        build_libs_common(icarus_build_dir)
        libvpi_icarus = Extension(
            "libvpi",
            define_macros=libvpi_define_macros,
            include_dirs=libvpi_include_dirs,
            libraries=libvpi_libraries + icarus_extra_lib,
            library_dirs=libvpi_library_dirs + icarus_extra_lib_path,
            sources=libvpi_sources,
            extra_link_args=libvpi_extra_link_args,
        )

        _build_lib(libvpi_icarus, dist, icarus_build_dir)

        _rename_safe(
            os.path.join(icarus_build_dir, "libvpi." + ext_name),
            os.path.join(icarus_build_dir, "libvpi.vpl"),
        )

    # For Questa
    questa_extra_lib = []
    questa_extra_lib_path = []
    questa_compile = True
    vsim_path = find_executable("vsim")
    questa_build_dir = os.path.join(build_dir_abs, "questa")
    libvpi_library_dirs = [questa_build_dir]

    if os.name == "nt":
        if vsim_path is None:
            logger.warning(
                "Questa (vsim) executable not found. VPI interface will not be avaliable."
            )
            questa_compile = False
        else:
            questa_path = os.path.dirname(vsim_path)
            questa_extra_lib = ["mtipli"]
            questa_extra_lib_path = [questa_path]

    if questa_compile:
        build_libs_common(questa_build_dir)
        libvpi_questa = Extension(
            "libvpi",
            define_macros=libvpi_define_macros,
            include_dirs=libvpi_include_dirs,
            libraries=libvpi_libraries + questa_extra_lib,
            library_dirs=libvpi_library_dirs + questa_extra_lib_path,
            sources=libvpi_sources,
            extra_link_args=libvpi_extra_link_args,
        )

        _build_lib(libvpi_questa, dist, questa_build_dir)

    if vsim_path is None:
        logger.warning(
            "Questa (vsim) executable not found. FLI interface will not be avaliable."
        )
    else:
        questa_path = os.path.dirname(os.path.dirname(vsim_path))
        libfli = Extension(
            "libfli",
            include_dirs=[include_dir, os.path.join(questa_path, "include")],
            libraries=["gpi", "gpilog", "stdc++"] + questa_extra_lib,
            library_dirs=libvpi_library_dirs + questa_extra_lib_path,
            sources=[
                os.path.join(share_lib_dir, "fli", "FliImpl.cpp"),
                os.path.join(share_lib_dir, "fli", "FliCbHdl.cpp"),
                os.path.join(share_lib_dir, "fli", "FliObjHdl.cpp"),
            ],
            extra_link_args=["-Wl,-rpath,$ORIGIN"],
        )

        _build_lib(libfli, dist, questa_build_dir)

    # For GHDL
    if os.name == "posix":
        ghdl_build_dir = os.path.join(build_dir_abs, "ghdl")
        build_libs_common(ghdl_build_dir)
        libvpi_library_dirs = [ghdl_build_dir]
        libvpi_ghdl = Extension(
            "libvpi",
            define_macros=libvpi_define_macros,
            include_dirs=libvpi_include_dirs,
            libraries=libvpi_libraries,
            library_dirs=libvpi_library_dirs,
            sources=libvpi_sources,
            extra_link_args=libvpi_extra_link_args,
        )
    
        _build_lib(libvpi_ghdl, dist, ghdl_build_dir)

    # For ius
    if os.name == "posix":
        ius_build_dir = os.path.join(build_dir_abs, "ius")
        build_libs_common(ius_build_dir)
        libvpi_library_dirs = [ius_build_dir]
        libvpi_ius = Extension(
            "libvpi",
            define_macros=libvpi_define_macros,
            include_dirs=libvpi_include_dirs,
            libraries=libvpi_libraries,
            library_dirs=libvpi_library_dirs,
            sources=libvpi_sources,
            extra_link_args=libvpi_extra_link_args,
        )

        _build_lib(libvpi_ius, dist, ius_build_dir)

        libvhpi_ius = Extension(
            "libvhpi",
            include_dirs=[include_dir],
            define_macros=[("VHPI_CHECKING", 1)],
            libraries=["gpi", "gpilog", "stdc++"],
            library_dirs=libvpi_library_dirs,
            sources=[
                os.path.join(share_lib_dir, "vhpi", "VhpiImpl.cpp"),
                os.path.join(share_lib_dir, "vhpi", "VhpiCbHdl.cpp"),
            ],
            extra_link_args=["-Wl,-rpath,$ORIGIN"],
        )

        _build_lib(libvhpi_ius, dist, ius_build_dir)

    # For vcs
    if os.name == "posix":
        vcs_build_dir = os.path.join(build_dir_abs, "vcs")
        build_libs_common(vcs_build_dir)
        libvpi_library_dirs = [vcs_build_dir]
        libvpi_vcs = Extension(
            "libvpi",
            define_macros=libvpi_define_macros,
            include_dirs=libvpi_include_dirs,
            libraries=libvpi_libraries,
            library_dirs=libvpi_library_dirs,
            sources=libvpi_sources,
            extra_link_args=libvpi_extra_link_args,
        )

        _build_lib(libvpi_vcs, dist, vcs_build_dir)

    return build_dir_abs, ext_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""Compile cocotb libraries.""")
    parser.add_argument(
        "--build-dir",
        # default = os.path.join(os.getcwd(), "cocotb_build"),
        default="cocotb_build",
        help="The directory to build the libraries into.",
    )
    args = parser.parse_args()
    build_libs(build_dir=args.build_dir)
