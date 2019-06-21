

import os
import cocotb
import pytest
import sys

from cocotb_test.run import Run

tests_dir = os.path.join(os.path.dirname(os.path.dirname(cocotb.__file__)), "tests")

if os.path.isdir(tests_dir) == False:
    raise IOError('Cocotb test directory not found. Plese download from git and install with `pip -e `')

def test_cocotb():
    Run(
        verilog_sources=
        [
            os.path.join(tests_dir, 'designs', 'sample_module', 'sample_module.sv')
        ],
        python_search=
        [
            os.path.join(tests_dir, 'test_cases', 'test_cocotb')
        ],
        toplevel='sample_module',
        module='test_cocotb'
    )

@pytest.mark.skip(sys.version_info >= (3, 5), reason="python3.5 api")
def test_cocotb_35():
    Run(
        verilog_sources=
        [
            os.path.join(tests_dir, 'designs', 'sample_module', 'sample_module.sv')
        ],
        python_search=
        [
            os.path.join(tests_dir, 'test_cases', 'test_cocotb')
        ],
        toplevel='sample_module',
        module='test_cocotb_35'
    )

def test_verilog_access():
    Run(
        verilog_sources=
        [
            os.path.join(tests_dir, 'designs', 'uart2bus', 'verilog', 'baud_gen.v'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'verilog', 'uart_parser.v'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'verilog', 'uart_rx.v'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'verilog', 'uart_tx.v'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'verilog', 'uart_top.v'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'verilog', 'uart2bus_top.v'),
            
            os.path.join(tests_dir, 'designs', 'uart2bus', 'top', 'verilog_toplevel.v'),
        ],
        vhdl_sources=
        [
            os.path.join(tests_dir, 'designs', 'uart2bus', 'vhdl', 'uart2BusTop_pkg.vhd'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'vhdl', 'baudGen.vhd'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'vhdl', 'uartParser.vhd'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'vhdl', 'uartRx.vhd'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'vhdl', 'uartTx.vhd'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'vhdl', 'uartTop.vhd'),
            os.path.join(tests_dir, 'designs', 'uart2bus', 'vhdl', 'uart2BusTop.vhd'),
        ],
        python_search=
        [
            os.path.join(tests_dir, 'test_cases', 'test_verilog_access')
        ],
        toplevel='verilog_toplevel',
        module='test_verilog_access'
    )

