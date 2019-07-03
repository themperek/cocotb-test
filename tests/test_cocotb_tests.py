import os
import cocotb
import pytest
import sys

from cocotb_test.run import run

tests_dir = os.path.join(os.path.dirname(os.path.dirname(cocotb.__file__)), "tests")

if os.path.isdir(tests_dir) == False:
    raise IOError(
        "Cocotb test directory not found. Please clone with git and install with `pip -e`"
    )


def test_cocotb():
    run(
        verilog_sources=[
            os.path.join(tests_dir, "designs", "sample_module", "sample_module.sv")
        ],
        python_search=[os.path.join(tests_dir, "test_cases", "test_cocotb")],
        toplevel="sample_module",
        module="test_cocotb",
    )

@pytest.mark.skipif(os.name == "nt", reason="Something wrong on Windows")
@pytest.mark.skipif(sys.version_info.major == 2, reason="python3.5 api")
def test_cocotb_35():
    run(
        verilog_sources=[
            os.path.join(tests_dir, "designs", "sample_module", "sample_module.sv")
        ],
        python_search=[os.path.join(tests_dir, "test_cases", "test_cocotb")],
        toplevel="sample_module",
        module="test_cocotb_35",
    )


@pytest.mark.skipif(os.environ["SIM"] == "icarus", reason="VHDL not suported")
def test_verilog_access():
    run(
        verilog_sources=[
            os.path.join(tests_dir, "designs", "uart2bus", "verilog", file)
            for file in [
                "baud_gen.v",
                "uart_parser.v",
                "uart_rx.v",
                "uart_tx.v",
                "uart_top.v",
                "uart2bus_top.v",
            ]
        ]
        + [os.path.join(tests_dir, "designs", "uart2bus", "top", "verilog_toplevel.v")],
        vhdl_sources=[
            os.path.join(
                tests_dir, "designs", "uart2bus", "vhdl", "uart2BusTop_pkg.vhd"
            ),
            os.path.join(tests_dir, "designs", "uart2bus", "vhdl", "baudGen.vhd"),
            os.path.join(tests_dir, "designs", "uart2bus", "vhdl", "uartParser.vhd"),
            os.path.join(tests_dir, "designs", "uart2bus", "vhdl", "uartRx.vhd"),
            os.path.join(tests_dir, "designs", "uart2bus", "vhdl", "uartTx.vhd"),
            os.path.join(tests_dir, "designs", "uart2bus", "vhdl", "uartTop.vhd"),
            os.path.join(tests_dir, "designs", "uart2bus", "vhdl", "uart2BusTop.vhd"),
        ],
        python_search=[os.path.join(tests_dir, "test_cases", "test_verilog_access")],
        toplevel="verilog_toplevel",
        module="test_verilog_access",
    )
