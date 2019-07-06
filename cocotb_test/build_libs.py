import os
import sys
import sysconfig
import cocotb
import errno
import distutils
import shutil

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


def _symlink_force(target, link_name):

    if os.name == "nt":  # On Windows there is an issue with symlink !Workaround'
        shutil.copy2(target, link_name)
        return

    try:
        os.symlink(target, link_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise e


def _build_lib(lib, dist, build_dir):

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
        _symlink_force(
            lib_path, os.path.join(os.path.abspath(dir_name), lib_name + "." + ext_name)
        )

    return dir_name, ext_name


def build_libs():

    cfg_vars = distutils.sysconfig.get_config_vars()
    for key, value in cfg_vars.items():
        if type(value) == str:
            cfg_vars[key] = value.replace("-Wstrict-prototypes", "")

    if sys.platform == "darwin":
        cfg_vars["LDSHARED"] = cfg_vars["LDSHARED"].replace("-bundle", "-dynamiclib")

    share_dir = os.path.join(os.path.dirname(cocotb.__file__), "share")
    share_lib_dir = os.path.join(share_dir, "lib")
    build_dir = os.path.join(os.getcwd(), "build")
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

    libcocotbutils = Extension(
        "libcocotbutils",
        include_dirs=[include_dir],
        sources=[os.path.join(share_lib_dir, "utils", "cocotb_utils.c")],
        extra_link_args=["-Wl,-rpath," + build_dir],
    )

    _build_lib(libcocotbutils, dist, build_dir)

    gpilog_ex_link_args = []
    if sys.platform == "darwin":
        gpilog_ex_link_args = ["-Wl,-rpath," + sysconfig.get_config_var("LIBDIR")]

    libgpilog = Extension(
        "libgpilog",
        include_dirs=[include_dir],
        libraries=[python_lib_link, "pthread", "m", "cocotbutils"],
        library_dirs=[build_dir],
        sources=[os.path.join(share_lib_dir, "gpi_log", "gpi_logging.c")],
        extra_link_args=gpilog_ex_link_args,
    )

    _build_lib(libgpilog, dist, build_dir)

    libcocotb = Extension(
        "libcocotb",
        define_macros=[("PYTHON_SO_LIB", python_lib)],
        include_dirs=[include_dir],
        library_dirs=[build_dir],
        libraries=["gpilog", "cocotbutils"],
        sources=[os.path.join(share_lib_dir, "embed", "gpi_embed.c")],
        extra_link_args=["-Wl,-rpath," + build_dir],
    )

    _build_lib(libcocotb, dist, build_dir)

    libgpi = Extension(
        "libgpi",
        define_macros=[("LIB_EXT", ext_name), ("SINGLETON_HANDLES", "")],
        include_dirs=[include_dir],
        libraries=["cocotbutils", "gpilog", "cocotb", "stdc++"],
        library_dirs=[build_dir],
        sources=[
            os.path.join(share_lib_dir, "gpi", "GpiCbHdl.cpp"),
            os.path.join(share_lib_dir, "gpi", "GpiCommon.cpp"),
        ],
        extra_link_args=["-Wl,-rpath," + build_dir],
    )

    _build_lib(libgpi, dist, build_dir)

    libsim = Extension(
        "simulator",
        include_dirs=[include_dir],
        libraries=["cocotbutils", "gpilog", "gpi"],
        library_dirs=[build_dir],
        sources=[os.path.join(share_lib_dir, "simulator", "simulatormodule.c")],
    )

    _build_lib(libsim, dist, build_dir)

    extra_lib = []
    extra_lib_path = []
    if os.environ["SIM"] == "icarus" and os.name == "nt":
        iverilog_path = find_executable("iverilog")
        if iverilog_path is None:
            raise ValueError("Icarus Verilog executable not found.")
        icarus_path = os.path.dirname(os.path.dirname(iverilog_path))
        extra_lib = ["vpi"]
        extra_lib_path = [os.path.join(icarus_path, "lib")]

    libvpi = Extension(
        "libvpi",
        define_macros=[("VPI_CHECKING", "1")],
        include_dirs=[include_dir],
        libraries=["gpi", "gpilog"] + extra_lib,
        library_dirs=[build_dir] + extra_lib_path,
        sources=[
            os.path.join(share_lib_dir, "vpi", "VpiImpl.cpp"),
            os.path.join(share_lib_dir, "vpi", "VpiCbHdl.cpp"),
        ],
        extra_link_args=["-Wl,-rpath," + build_dir],
    )

    _build_lib(libvpi, dist, build_dir)

    if os.name == "posix":
        libvhpi = Extension(
            "libvhpi",
            include_dirs=[include_dir],
            define_macros=[("VHPI_CHECKING", 1)],
            libraries=["gpi", "gpilog", "stdc++"],
            library_dirs=[build_dir],
            sources=[
                os.path.join(share_lib_dir, "vhpi", "VhpiImpl.cpp"),
                os.path.join(share_lib_dir, "vhpi", "VhpiCbHdl.cpp"),
            ],
            extra_link_args=["-Wl,-rpath," + build_dir],
        )

        _build_lib(libvhpi, dist, build_dir)

    if os.environ["SIM"] == "questa":
        vsim_path = find_executable("vsim")
        questa_path = os.path.dirname(os.path.dirname(vsim_path))

        libfli = Extension(
            "libfli",
            include_dirs=[include_dir, os.path.join(questa_path, "include")],
            libraries=["gpi", "gpilog", "stdc++"],
            library_dirs=[build_dir],
            sources=[
                os.path.join(share_lib_dir, "fli", "FliImpl.cpp"),
                os.path.join(share_lib_dir, "fli", "FliCbHdl.cpp"),
                os.path.join(share_lib_dir, "fli", "FliObjHdl.cpp"),
            ],
            extra_link_args=["-Wl,-rpath," + build_dir],
        )

        _build_lib(libfli, dist, build_dir)

    _symlink_force(
        os.path.join(build_dir, "libvpi." + ext_name),
        os.path.join(build_dir, "gpivpi.vpl"),
    )

    return build_dir, ext_name
