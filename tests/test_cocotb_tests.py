import os
import cocotb
import pytest
import sys

from cocotb_test.simulator import run

tests_dir = os.path.join(os.path.dirname(os.path.dirname(cocotb.__file__)), "tests")

if os.path.isdir(tests_dir) == False:
    raise IOError(
        "Cocotb test directory not found. Please clone with git and install with `pip -e`"
    )


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.skipif(os.getenv("SIM") in ["icarus", "verilator"] , reason="VHDL not supported")
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
        + [os.path.join(tests_dir, "designs", "uart2bus", "top", "verilog_toplevel.sv")],
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
