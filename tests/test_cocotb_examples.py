

import os
import cocotb
import pytest

from cocotb_test.run import Run

example_dir = os.path.join(os.path.dirname(os.path.dirname(cocotb.__file__)), "examples")

if os.path.isdir(example_dir) == False:
    raise IOError('Cocotb example directory not found. Plese download from git and install with `pip -e `')


def test_ping_tun_tap():
    if not (os.name == 'posix' and os.geteuid() == 0):
        pytest.skip("This test works only on POSIX os with admin rights")
        
    Run(
        verilog_sources=[os.path.join(example_dir, 'ping_tun_tap', 'hdl', 'icmp_reply.sv')],
        toplevel='icmp_reply',
        python_search=[os.path.join(example_dir, 'ping_tun_tap', 'tests')],
        module='test_icmp_reply'
        )


def test_dff_verilog():
    Run(
        verilog_sources=[os.path.join(example_dir, 'dff', 'hdl', 'dff.v')],
        toplevel='dff',
        python_search=[os.path.join(example_dir, 'dff', 'tests')],
        module='dff_cocotb'
    )


def test_dff_vhdl():
    Run(
        vhdl_sources=[os.path.join(example_dir, 'dff', 'hdl', 'dff.vhdl')],
        toplevel='dff',
        python_search=[os.path.join(example_dir, 'dff', 'tests')],
        module='dff_cocotb',
        toplevel_lang='vhdl'
    )


def test_adder_verilog():
    Run(
        verilog_sources=[os.path.join(example_dir, 'adder', 'hdl', 'adder.v')],
        toplevel='adder',
        python_search=
        [
            os.path.join(example_dir, 'adder', 'tests'),
            os.path.join(example_dir, 'adder', 'model'),
        ],
        module='test_adder'
    )


def test_adder_vhdl():
    Run(
        vhdl_sources=[os.path.join(example_dir, 'adder', 'hdl', 'adder.vhdl')],
        toplevel='adder',
        python_search=
        [
            os.path.join(example_dir, 'adder', 'tests'),
            os.path.join(example_dir, 'adder', 'model'),
        ],
        module='test_adder',
        toplevel_lang='vhdl'
    )


def test_mean():
    Run(
        vhdl_sources=
        [
            os.path.join(example_dir, 'mean', 'hdl', 'mean_pkg.vhd'),
            os.path.join(example_dir, 'mean', 'hdl', 'mean.vhd'),
        ],
        verilog_sources=
        [
            os.path.join(example_dir, 'mean', 'hdl', 'mean_sv.sv')
        ],
        toplevel='mean_sv',
        python_search=
        [
            os.path.join(example_dir, 'mean', 'tests'),
        ],
        module='test_mean',
    )

    
def test_mixed_top_verilog():
    Run(
        vhdl_sources=
        [
            os.path.join(example_dir, 'endian_swapper', 'hdl', 'endian_swapper.vhdl'),
        ],
        verilog_sources=
        [
            os.path.join(example_dir, 'endian_swapper', 'hdl', 'endian_swapper.sv'),
            os.path.join(example_dir, 'mixed_language', 'hdl', 'toplevel.sv')
        ],
        toplevel='endian_swapper_mixed',
        python_search=
        [
            os.path.join(example_dir, 'mixed_language', 'tests'),
        ],
        module='test_mixed_language',
    )

    
def test_mixed_top_vhdl():
    Run(
        vhdl_sources=
        [
            os.path.join(example_dir, 'endian_swapper', 'hdl', 'endian_swapper.vhdl'),
            os.path.join(example_dir, 'mixed_language', 'hdl', 'toplevel.vhdl')
        ],
        verilog_sources=
        [
            os.path.join(example_dir, 'endian_swapper', 'hdl', 'endian_swapper.sv'),
        ],
        toplevel='endian_swapper_mixed',
        python_search=
        [
            os.path.join(example_dir, 'mixed_language', 'tests'),
        ],
        module='test_mixed_language',
        toplevel_lang='vhdl'
    )

    
def test_axi_lite_slave():
    Run(
        verilog_sources=
        [
            os.path.join(example_dir, 'axi_lite_slave', 'hdl', 'axi_lite_slave.v'),
            os.path.join(example_dir, 'axi_lite_slave', 'hdl', 'axi_lite_demo.v'),
            os.path.join(example_dir, 'axi_lite_slave', 'hdl', 'tb_axi_lite_slave.v'),
        ],
        toplevel='tb_axi_lite_slave',
        include_dir=
        [
            os.path.join(example_dir, 'axi_lite_slave', 'hdl'),
        ],
        python_search=
        [
            os.path.join(example_dir, 'axi_lite_slave', 'tests'),
        ],
        module='test_axi_lite_slave',
    )


def test_endian_swapper_verilog():
    Run(
        verilog_sources=
        [
            os.path.join(example_dir, 'endian_swapper', 'hdl', 'endian_swapper.sv'),
        ],
        toplevel='endian_swapper_sv',
        python_search=
        [
            os.path.join(example_dir, 'endian_swapper', 'tests'),
        ],
        module='test_endian_swapper',
    )


def test_endian_swapper_vhdl():
    Run(
        vhdl_sources=
        [
            os.path.join(example_dir, 'endian_swapper', 'hdl', 'endian_swapper.vhdl'),
        ],
        toplevel='endian_swapper_vhdl',
        python_search=
        [
            os.path.join(example_dir, 'endian_swapper', 'tests'),
        ],
        module='test_endian_swapper',
        toplevel_lang='vhdl'
    )

