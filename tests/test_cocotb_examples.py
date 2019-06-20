

import os
import cocotb
import pytest

from cocotb_test.run import Run

example_dir = os.path.join(os.path.dirname(os.path.dirname(cocotb.__file__)), "examples")

if os.path.isdir(example_dir) == False:
    raise IOError('Cocotb example directory not found. Plese download from git and install with `pip -e `')


def test_ping_tun_tap():
    if not ( os.name == 'posix' and os.geteuid() == 0):
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
        toplevel_lang = 'vhdl'
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
        toplevel_lang = 'vhdl'
    )