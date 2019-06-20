"""A run class."""

import subprocess
import os
import sys
import sysconfig
import cocotb
import errno
import distutils
import inspect

from setuptools import Extension
from setuptools.command.build_ext import build_ext
from setuptools.dist import Distribution

from xml.etree import cElementTree as ET
import pytest 
from distutils.spawn import find_executable
        
cfg_vars = distutils.sysconfig.get_config_vars()
for key, value in cfg_vars.items():
    if type(value) == str:
        cfg_vars[key] = value.replace("-Wstrict-prototypes", "")


def _symlink_force(target, link_name):
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

    # print("Building:", out_lib[0])

    target = os.path.join(os.path.abspath(dir_name), lib_name + "." + ext_name)
    if target != lib_path:
        _symlink_force(
            lib_path, os.path.join(os.path.abspath(dir_name), lib_name + "." + ext_name)
        )

    return dir_name, ext_name


def build_libs():
    share_dir = os.path.join(os.path.dirname(cocotb.__file__), "share")

    python_lib = sysconfig.get_config_var("LDLIBRARY")
    python_lib_link = os.path.splitext(python_lib)[0][3:]

    dist = Distribution()
    dist.parse_config_files()

    libcocotbutils = Extension(
        "libcocotbutils",
        include_dirs=[share_dir + "/include"],
        sources=[share_dir + "/lib/utils/cocotb_utils.c"],
    )

    lib_path, ext_name = _build_lib(libcocotbutils, dist)

    libgpilog = Extension(
        "libgpilog",
        # define_macros=[("MODELSIM",),("VPI_CHECKING",)],
        include_dirs=[share_dir + "/include"],
        libraries=[python_lib_link, "pthread", "dl", "util", "rt", "m", "cocotbutils"],
        library_dirs=[lib_path],
        sources=[share_dir + "/lib/gpi_log/gpi_logging.c"],
    )

    _build_lib(libgpilog, dist)

    libcocotb = Extension(
        "libcocotb",
        # define_macros=[("MODELSIM",),("VPI_CHECKING",),("PYTHON_SO_LIB", python_lib)],
        define_macros=[("PYTHON_SO_LIB", python_lib)],
        include_dirs=[share_dir + "/include"],
        sources=[share_dir + "/lib/embed/gpi_embed.c"],
    )

    _build_lib(libcocotb, dist)

    libgpi = Extension(
        "libgpi",
        # define_macros=[("MODELSIM",),("VPI_CHECKING",)],
        define_macros=[("LIB_EXT",ext_name)],
        include_dirs=[share_dir + "/include"],
        libraries=["cocotbutils", "gpilog", "cocotb", "stdc++"],
        library_dirs=[lib_path],
        sources=[
            share_dir + "/lib/gpi/GpiCbHdl.cpp",
            share_dir + "/lib/gpi/GpiCommon.cpp",
        ],
    )

    _build_lib(libgpi, dist)

    libsim = Extension(
        "simulator",
        # define_macros=[("MODELSIM",),("VPI_CHECKING",)],
        include_dirs=[share_dir + "/include"],
        libraries=["cocotbutils", "gpilog", "gpi"],
        library_dirs=[lib_path],
        sources=[share_dir + "/lib/simulator/simulatormodule.c"],
    )

    _build_lib(libsim, dist)

    libvpi = Extension(
        "libvpi",
        # define_macros=[("MODELSIM",),("VPI_CHECKING",)],
        include_dirs=[share_dir + "/include"],
        libraries=["gpi", "gpilog"],
        library_dirs=[lib_path],
        sources=[
            share_dir + "/lib/vpi/VpiImpl.cpp",
            share_dir + "/lib/vpi/VpiCbHdl.cpp",
        ],
    )

    _build_lib(libvpi, dist)
 
    libvhpi = Extension(
            "libvhpi",
            include_dirs=[
                share_dir + "/include"
            ],
            
            define_macros=[("VHPI_CHECKING",)],
            libraries=["gpilog", "gpi", "stdc++"],
            library_dirs=[lib_path],
            sources=[
                share_dir + "/lib/vhpi/VhpiImpl.cpp",
                share_dir + "/lib/vhpi/VhpiCbHdl.cpp",
            ],
        )
    
    _build_lib(libvhpi, dist)
        
    if os.environ['SIM'] == 'questa':
        vsim_path = find_executable('vsim')
        questa_path = os.path.dirname(os.path.dirname(vsim_path))
    
        libfli = Extension(
            "libfli",
            # define_macros=[("MODELSIM",),("VPI_CHECKING",)],
            include_dirs=[
                share_dir + "/include",
                os.path.join(questa_path, "include",)
            ],
            libraries=["gpilog", "gpi", "stdc++"],
            library_dirs=[lib_path],
            sources=[
                share_dir + "/lib/fli/FliImpl.cpp",
                share_dir + "/lib/fli/FliCbHdl.cpp",
                share_dir + "/lib/fli/FliObjHdl.cpp",
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


def _run_vcs(toplevel, libs_dir, verilog_sources_abs, sim_build_dir):
    
    pli_cmd = "acc+=rw,wn:*" 
    
    do_file_path = os.path.join(sim_build_dir, 'pli.tab')
    with open(do_file_path, 'w') as pli_file:
        pli_file.write(pli_cmd)

    comp_cmd = ["vcs", "-full64", "-debug", "+vpi" , "-P", "pli.tab", "-sverilog", "+define+COCOTB_SIM=1", "-load", "libvpi.so"] + verilog_sources_abs
    print(" ".join(comp_cmd))
    process = subprocess.check_call(comp_cmd, cwd=sim_build_dir)
    
    cmd = [os.path.join(sim_build_dir, "simv") , "+define+COCOTB_SIM=1"]
    print (" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_ius(toplevel, libs_dir, verilog_sources_abs, vhdl_sources_abs, sim_build_dir):

    #cmd = ["irun", "-64", "-v93", "+access+rwc", "-loadvpi", os.path.join(libs_dir, "libvpi.so") + "", "-top", toplevel] + verilog_sources_abs + vhdl_sources_abs
    #cmd = ["irun", "-64", "-v93", '-plinowarn', "+access+rwc", "-top", toplevel] + verilog_sources_abs + vhdl_sources_abs

    os.environ["GPI_EXTRA"] = 'vhpi'
    
    cmd = ["irun", "-64", "-v93", '-plinowarn', "+access+rwc", "-top", toplevel] + verilog_sources_abs + vhdl_sources_abs
    
    
    print (" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)

    
def _run_icarus(toplevel, libs_dir, verilog_sources_abs, sim_build_dir):
    
    sim_compile_file = os.path.join(sim_build_dir, "sim.vvp")

    comp_cmd = ["iverilog", "-o", sim_compile_file, "-D", "COCOTB_SIM=1", "-s", toplevel, "-g2012"] + verilog_sources_abs
    print(" ".join(comp_cmd))
    process = subprocess.check_call(comp_cmd)
    
    cmd = ["vvp", "-M", libs_dir, "-m", "gpivpi", sim_compile_file]
    print (" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)


def _run_questa(toplevel, libs_dir, verilog_sources_abs, vhdl_sources_abs, sim_build_dir, ext_name, toplevel_lang):

    do_script = '''# Autogenerated file
    onerror {
        quit -f -code 1
    }
    '''
    if verilog_sources_abs:
        do_script += 'vlog +define+COCOTB_SIM -sv {VERILOG_SOURCES}\n'.format(VERILOG_SOURCES=" ".join(verilog_sources_abs))
        
    if vhdl_sources_abs:
        do_script += 'vcom +define+COCOTB_SIM {VHDL_SOURCES}\n'.format(VHDL_SOURCES=" ".join(vhdl_sources_abs))
    
    if toplevel_lang=='vhdl':
        do_script += 'vsim -onfinish exit -foreign "cocotb_init libfli.{EXT_NAME}" {TOPLEVEL}\n'.format(TOPLEVEL=toplevel, EXT_NAME=ext_name)
    else:
        do_script += 'vsim -onfinish exit -pli libvpi.{EXT_NAME} {TOPLEVEL}\n'.format(TOPLEVEL=toplevel, EXT_NAME=ext_name)
    
    do_script += '''log -recursive /*
    onbreak resume
    run -all
    quit
    '''
    
    do_file_path = os.path.join(sim_build_dir, 'runsim.do')
    with open(do_file_path, 'w') as do_file:
        do_file.write(do_script)
    
    cmd = ["vsim", "-c", "-do", 'runsim.do']
    print (" ".join(cmd))
    process = subprocess.check_call(cmd, cwd=sim_build_dir)

    
def Run(toplevel, verilog_sources=[], vhdl_sources=[], module=None, python_search=[], toplevel_lang='verilog'):

    if vhdl_sources:
        if os.environ['SIM'] == 'icarus' or os.environ['SIM'] == 'vcs':
            pytest.skip("This simulator does not support VHDL")

    libs_dir, ext_name = build_libs()

    previous_frame = inspect.currentframe().f_back
    (run_module_filename, _, _, _, _) = inspect.getframeinfo(previous_frame)

    run_dir_name = os.path.dirname(run_module_filename)
    run_module_name = os.path.splitext(os.path.split(run_module_filename)[-1])[0]

    if module is None:
        module = run_module_name

    my_env = os.environ
    my_env["LD_LIBRARY_PATH"] = libs_dir + ":" + sysconfig.get_config_var("LIBDIR")

    python_path = ":".join(sys.path)
    my_env["PYTHONPATH"] = python_path + ":" + libs_dir
    
    for path in python_search:
        my_env["PYTHONPATH"] += ':' + path
        
    my_env["TOPLEVEL"] = toplevel
    # my_env["TOPLEVEL_LANG"] = "verilog"
    my_env["COCOTB_SIM"] = "1"
    my_env["MODULE"] = module

    
    sim_build_dir = os.path.abspath(os.path.join(run_dir_name, "sim_build"))
    if not os.path.exists(sim_build_dir):
        os.makedirs(sim_build_dir)

    verilog_sources_abs = []
    for src in verilog_sources:
        verilog_sources_abs.append(os.path.abspath(os.path.join(run_dir_name, src)))

    vhdl_sources_abs = []
    for src in vhdl_sources:
        vhdl_sources_abs.append(os.path.abspath(os.path.join(run_dir_name, src)))

    results_xml_file = os.path.join(sim_build_dir, 'results.xml')

    if os.path.isfile(results_xml_file):
        os.remove(results_xml_file)
    
    if my_env['SIM'] == 'icarus':
        _run_icarus(toplevel, libs_dir, verilog_sources_abs, sim_build_dir)
    elif my_env['SIM'] == 'questa':
        _run_questa(toplevel, libs_dir, verilog_sources_abs, vhdl_sources_abs, sim_build_dir, ext_name, toplevel_lang)
    elif my_env['SIM'] == 'ius':
        _run_ius(toplevel, libs_dir, verilog_sources_abs, vhdl_sources_abs, sim_build_dir)
    elif my_env['SIM'] == 'vcs':
        _run_vcs(toplevel, libs_dir, verilog_sources_abs, sim_build_dir)
    else:
        raise NotImplementedError("Set SIM variable. Supported: icarus, questa, ius, vcs")

    tree = ET.parse(results_xml_file)
    for ts in tree.iter("testsuite"):
        for tc in ts.iter('testcase'):
            for failure in tc.iter('failure'):
                raise ValueError('{} class="{}" test="{}" error={}'.format(failure.get('message'), tc.get('classname'), tc.get('name'), failure.get('stdout')))
            
