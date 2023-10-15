import os
import cocotb
import pytest

from cocotb_test.simulator import run

example_dir = os.path.join(os.path.dirname(os.path.dirname(cocotb.__file__)), "examples")

if os.path.isdir(example_dir) == False:
    raise IOError("Cocotb example directory not found. Please clone with git and install with `pip -e`")


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
def test_adder_verilog():
    run(
        verilog_sources=[os.path.join(example_dir, "adder", "hdl", "adder.sv")],
        toplevel="adder",
        python_search=[os.path.join(example_dir, "adder", "tests"), os.path.join(example_dir, "adder", "model")],
        module="test_adder",
        force_compile=True,
    )


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Errors in compilation cocotb example")
@pytest.mark.skipif(os.getenv("SIM") in ["icarus", "verilator"], reason="VHDL not supported")
def test_adder_vhdl():
    run(
        vhdl_sources=[os.path.join(example_dir, "adder", "hdl", "adder.vhdl")],
        toplevel="adder",
        python_search=[os.path.join(example_dir, "adder", "tests"), os.path.join(example_dir, "adder", "model")],
        module="test_adder",
        toplevel_lang="vhdl",
        force_compile=True,
    )
