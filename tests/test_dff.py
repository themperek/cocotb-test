from cocotb_test.run import run
import pytest
import os

@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
#@pytest.mark.parametrize("seed", range(10))
def test_dff_verilog():
    run(verilog_sources=["dff.v"], toplevel="dff_test", module="dff_cocotb")  # sources  # top level HDL  # name of cocotb test module


@pytest.mark.skipif(os.getenv("SIM") == "verilator", reason="VHDL not suported")
@pytest.mark.skipif(os.getenv("SIM") == "icarus", reason="VHDL not suported")
def test_dff_vhdl():
    run(vhdl_sources=["dff.vhdl"], toplevel="dff_test_vhdl", module="dff_cocotb", toplevel_lang="vhdl")


if __name__ == "__main__":
    test_dff_verilog()
