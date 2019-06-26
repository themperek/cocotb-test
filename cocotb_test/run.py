"""A run class."""

import subprocess
import os
import sys
import sysconfig
import cocotb
import errno
import distutils
import inspect
import shutil

if sys.version_info.major >= 3:
    from tkinter import _stringify as as_tcl_value
else:
    from Tkinter import _stringify as as_tcl_value

# import distutils.log
# distutils.log.set_verbosity(-1) # Disable logging in disutils
# distutils.log.set_verbosity(distutils.log.DEBUG) # Set DEBUG level

from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution

from xml.etree import cElementTree as ET
import pytest
from distutils.spawn import find_executable
import pkg_resources

# A HACK to solve the problem on Windows: https://stackoverflow.com/questions/34689210/error-exporting-symbol-when-building-python-c-extension-in-windows
from distutils.command.build_ext import build_ext as _du_build_ext
from unittest.mock import Mock

mockobj = _du_build_ext
mockobj.get_export_symbols = Mock(return_value=None)

cfg_vars = distutils.sysconfig.get_config_vars()
for key, value in cfg_vars.items():
    if type(value) == str:
        cfg_vars[key] = value.replace("-Wstrict-prototypes", "")


def _symlink_force(target, link_name):

    if os.name == "nt":  # On windows we there is an issue with simplink !Workaround'
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


def _build_lib(lib, dist):
    dist.ext_modules = [lib]
    _build_ext = build_ext(dist)
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
    share_dir = os.path.join(os.path.dirname(cocotb.__file__), "share")
    share_lib_dir = os.path.join(share_dir, "lib")

    if os.name == "nt":
        python_version = distutils.sysconfig.get_python_version()
        python_version.replace(".", "")
        python_lib = "python" + python_version + ".dll"
        python_lib_link = python_lib.split(".")[0]
    else:
        python_lib = sysconfig.get_config_var("LDLIBRARY")
        python_lib_link = os.path.splitext(python_lib)[0][3:]

    include_dir = os.path.join(share_dir, "include")

    dist = Distribution()
    dist.parse_config_files()

    libcocotbutils = Extension(
        "libcocotbutils",
        include_dirs=[include_dir],
        sources=[os.path.join(share_lib_dir, "utils", "cocotb_utils.c")],
    )

    lib_path, ext_name = _build_lib(libcocotbutils, dist)

    libgpilog = Extension(
        "libgpilog",
        include_dirs=[include_dir],
        libraries=[
            python_lib_link,
            "pthread",
            "m",
            "cocotbutils",
        ],  # + ["dl", "util", "rt"],
        library_dirs=[lib_path],
        sources=[os.path.join(share_lib_dir, "gpi_log", "gpi_logging.c")],
    )

    _build_lib(libgpilog, dist)

    libcocotb = Extension(
        "libcocotb",
        define_macros=[("PYTHON_SO_LIB", python_lib)],
        include_dirs=[include_dir],
        library_dirs=[lib_path],
        libraries=["gpilog", "cocotbutils"],
        sources=[os.path.join(share_lib_dir, "embed", "gpi_embed.c")],
    )

    _build_lib(libcocotb, dist)

    libgpi = Extension(
        "libgpi",
        define_macros=[("LIB_EXT", ext_name), ("SINGLETON_HANDLES", "")],
        include_dirs=[include_dir],
        libraries=["cocotbutils", "gpilog", "cocotb", "stdc++"],
        library_dirs=[lib_path],
        sources=[
            os.path.join(share_lib_dir, "gpi", "GpiCbHdl.cpp"),
            os.path.join(share_lib_dir, "gpi", "GpiCommon.cpp"),
        ],
    )

    _build_lib(libgpi, dist)

    libsim = Extension(
        "simulator",
        include_dirs=[include_dir],
        libraries=["cocotbutils", "gpilog", "gpi"],
        library_dirs=[lib_path],
        sources=[os.path.join(share_lib_dir, "simulator", "simulatormodule.c")],
    )

    _build_lib(libsim, dist)

    extra_lib = []
    extra_lib_path = []
    if os.environ["SIM"] == "icarus" and os.name == "nt":
        iverilog_path = find_executable("iverilog__")
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
        library_dirs=[lib_path] + extra_lib_path,
        sources=[
            os.path.join(share_lib_dir, "vpi", "VpiImpl.cpp"),
            os.path.join(share_lib_dir, "vpi", "VpiCbHdl.cpp"),
        ],
    )

    _build_lib(libvpi, dist)

    if os.name == "posix":
        libvhpi = Extension(
            "libvhpi",
            include_dirs=[include_dir],
            define_macros=[("VHPI_CHECKING", 1)],
            libraries=["gpilog", "gpi", "stdc++"],
            library_dirs=[lib_path],
            sources=[
                os.path.join(share_lib_dir, "vhpi", "VhpiImpl.cpp"),
                os.path.join(share_lib_dir, "vhpi", "VhpiCbHdl.cpp"),
            ],
        )

        _build_lib(libvhpi, dist)

    if os.environ["SIM"] == "questa":
        vsim_path = find_executable("vsim")
        questa_path = os.path.dirname(os.path.dirname(vsim_path))

        libfli = Extension(
            "libfli",
            include_dirs=[include_dir, os.path.join(questa_path, "include")],
            libraries=["gpilog", "gpi", "stdc++"],
            library_dirs=[lib_path],
            sources=[
                os.path.join(share_lib_dir, "fli", "FliImpl.cpp"),
                os.path.join(share_lib_dir, "fli", "FliCbHdl.cpp"),
                os.path.join(share_lib_dir, "fli", "FliObjHdl.cpp"),
            ],
        )

        _build_lib(libfli, dist)

    _symlink_force(
        os.path.join(lib_path, "libvpi." + ext_name),
        os.path.join(lib_path, "gpivpi.vpl"),
    )
    _symlink_force(
        os.path.join(lib_path, "libvpi." + ext_name),
        os.path.join(lib_path, "cocotb.vpl"),
    )

    return lib_path, ext_name


def _run_vcs(toplevel, libs_dir, verilog_sources_abs, sim_build_dir, include_dir_abs):

    pli_cmd = "acc+=rw,wn:*"

    inculde_dir_cmd = []
    for dir in include_dir_abs:
        inculde_dir_cmd.append("+incdir+" + dir)

    do_file_path = os.path.join(sim_build_dir, "pli.tab")
    with open(do_file_path, "w") as pli_file:
        pli_file.write(pli_cmd)

    comp_cmd = (
        [
            "vcs",
            "-full64",
            "-debug",
            "+vpi",
            "-P",
            "pli.tab",
            "-sverilog",
            "+define+COCOTB_SIM=1",
            "-load",
            "libvpi.so",
        ]
        + inculde_dir_cmd
        + verilog_sources_abs
    )
    print(" ".join(comp_cmd))
    process = subprocess.check_call(comp_cmd, cwd=sim_build_dir)

    cmd = [os.path.join(sim_build_dir, "simv"), "+define+COCOTB_SIM=1"]
    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_ius(
    toplevel,
    libs_dir,
    verilog_sources_abs,
    vhdl_sources_abs,
    sim_build_dir,
    include_dir_abs,
):

    os.environ["GPI_EXTRA"] = "vhpi"

    include_dir_cmd = []
    for dir in include_dir_abs:
        include_dir_cmd.append("+incdir+" + dir)

    cmd = (
        [
            "irun",
            "-64",
            "-define",
            "COCOTB_SIM=1",
            "-v93",
            "-plinowarn",
            "+access+rwc",
            "-top",
            toplevel,
        ]
        + include_dir_cmd
        + vhdl_sources_abs
        + verilog_sources_abs
    )

    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_icarus(
    toplevel, libs_dir, verilog_sources_abs, sim_build_dir, include_dir_abs
):

    sim_compile_file = os.path.join(sim_build_dir, "sim.vvp")

    inculde_dir_cmd = []
    for dir in include_dir_abs:
        inculde_dir_cmd.append("-I")
        inculde_dir_cmd.append(dir)

    comp_cmd = (
        [
            "iverilog",
            "-o",
            sim_compile_file,
            "-D",
            "COCOTB_SIM=1",
            "-s",
            toplevel,
            "-g2012",
        ]
        + inculde_dir_cmd
        + verilog_sources_abs
    )
    print(" ".join(comp_cmd))
    process = subprocess.check_call(comp_cmd)

    cmd = ["vvp", "-M", libs_dir, "-m", "gpivpi", sim_compile_file]
    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_questa(
    toplevel,
    libs_dir,
    verilog_sources_abs,
    vhdl_sources_abs,
    sim_build_dir,
    ext_name,
    toplevel_lang,
    include_dir_abs,
):

    inculde_dir_cmd = []
    for dir in include_dir_abs:
        inculde_dir_cmd.append("+incdir+" + dir)

    do_script = """# Autogenerated file
    onerror {
        quit -f -code 1
    }
    """

    if vhdl_sources_abs:
        do_script += "vcom -mixedsvvh +define+COCOTB_SIM {INCDIR} {VHDL_SOURCES}\n".format(
            VHDL_SOURCES=as_tcl_value(vhdl_sources_abs),
            INCDIR=as_tcl_value(inculde_dir_cmd),
        )
        os.environ["GPI_EXTRA"] = "fli"

    if verilog_sources_abs:
        do_script += "vlog -mixedsvvh +define+COCOTB_SIM -sv {INCDIR} {VERILOG_SOURCES}\n".format(
            VERILOG_SOURCES=as_tcl_value(verilog_sources_abs),
            INCDIR=as_tcl_value(inculde_dir_cmd),
        )

    if toplevel_lang == "vhdl":
        do_script += "vsim -onfinish exit -foreign {EXT_NAME} {TOPLEVEL}\n".format(
            TOPLEVEL=as_tcl_value(toplevel),
            EXT_NAME=as_tcl_value("cocotb_init libfli.{}".format(ext_name)),
        )
    else:
        do_script += "vsim -onfinish exit -pli {EXT_NAME} {TOPLEVEL}\n".format(
            TOPLEVEL=as_tcl_value(toplevel),
            EXT_NAME=as_tcl_value("libvli.{}".format(ext_name)),
        )

    do_script += """log -recursive /*
    onbreak resume
    run -all
    quit
    """

    do_file_path = os.path.join(sim_build_dir, "runsim.do")
    with open(do_file_path, "w") as do_file:
        do_file.write(do_script)

    cmd = ["vsim", "-c", "-do", "runsim.do"]
    print(" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def Run(
    toplevel,
    verilog_sources=[],
    vhdl_sources=[],
    module=None,
    python_search=[],
    toplevel_lang="verilog",
    include_dir=[],
):

    supported_sim = ["icarus", "questa", "ius", "vcs"]
    if "SIM" in os.environ and os.environ["SIM"] in supported_sim:
        pass
    else:
        raise NotImplementedError(
            "Set SIM variable. Supported: " + ", ".join(supported_sim)
        )

    if vhdl_sources:
        if os.environ["SIM"] == "icarus" or os.environ["SIM"] == "vcs":
            pytest.skip("This simulator does not support VHDL")

    libs_dir, ext_name = build_libs()

    previous_frame = inspect.currentframe().f_back
    (run_module_filename, _, _, _, _) = inspect.getframeinfo(previous_frame)

    run_dir_name = os.path.dirname(run_module_filename)
    run_module_name = os.path.splitext(os.path.split(run_module_filename)[-1])[0]

    if module is None:
        module = run_module_name

    my_env = os.environ
    my_env["LD_LIBRARY_PATH"] = libs_dir
    if os.name == "posix":
        my_env["LD_LIBRARY_PATH"] += os.pathsep + sysconfig.get_config_var("LIBDIR")

    my_env["PATH"] += os.pathsep + libs_dir

    python_path = os.pathsep.join(sys.path)
    my_env["PYTHONPATH"] = os.pathsep + python_path + os.pathsep + libs_dir

    for path in python_search:
        my_env["PYTHONPATH"] += os.pathsep + path

    my_env["TOPLEVEL"] = toplevel
    # my_env["TOPLEVEL_LANG"] = "verilog"
    my_env["COCOTB_SIM"] = "1"
    my_env["MODULE"] = module
    my_env["VERSION"] = pkg_resources.get_distribution("cocotb").version

    sim_build_dir = os.path.abspath(os.path.join(run_dir_name, "sim_build"))
    if not os.path.exists(sim_build_dir):
        os.makedirs(sim_build_dir)

    verilog_sources_abs = []
    for src in verilog_sources:
        verilog_sources_abs.append(os.path.abspath(os.path.join(run_dir_name, src)))

    vhdl_sources_abs = []
    for src in vhdl_sources:
        vhdl_sources_abs.append(os.path.abspath(os.path.join(run_dir_name, src)))

    include_dir_abs = []
    for dir in include_dir:
        include_dir_abs.append(os.path.abspath(dir))

    results_xml_file = os.path.join(sim_build_dir, "results.xml")

    if os.path.isfile(results_xml_file):
        os.remove(results_xml_file)

    if my_env["SIM"] == "icarus":
        _run_icarus(
            toplevel, libs_dir, verilog_sources_abs, sim_build_dir, include_dir_abs
        )
    elif my_env["SIM"] == "questa":
        _run_questa(
            toplevel,
            libs_dir,
            verilog_sources_abs,
            vhdl_sources_abs,
            sim_build_dir,
            ext_name,
            toplevel_lang,
            include_dir_abs,
        )
    elif my_env["SIM"] == "ius":
        _run_ius(
            toplevel,
            libs_dir,
            verilog_sources_abs,
            vhdl_sources_abs,
            sim_build_dir,
            include_dir_abs,
        )
    elif my_env["SIM"] == "vcs":
        _run_vcs(
            toplevel, libs_dir, verilog_sources_abs, sim_build_dir, include_dir_abs
        )

    tree = ET.parse(results_xml_file)
    for ts in tree.iter("testsuite"):
        for tc in ts.iter("testcase"):
            for failure in tc.iter("failure"):
                # raise ValueError('{} class="{}" test="{}" error={}'.format(failure.get('message'), tc.get('classname'), tc.get('name'), failure.get('stdout')))
                pytest.fail(
                    '{} class="{}" test="{}" error={}'.format(
                        failure.get("message"),
                        tc.get("classname"),
                        tc.get("name"),
                        failure.get("stdout"),
                    )
                )
