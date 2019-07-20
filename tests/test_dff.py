from cocotb_test.run import run
import pytest
import os


@pytest.mark.skipif(os.environ["SIM"] == "ghdl", reason="Verilog not suported")
def test_dff():
    run(
        verilog_sources=["dff.v"],  # sources
        toplevel="dff",  # top level HDL
        module="dff_cocotb",  # name of cocotb test module
    )


@pytest.mark.skipif(os.environ["SIM"] == "icarus", reason="VHDL not suported")
def test_dff_vhdl():
    run(vhdl_sources=["dff.vhdl"], toplevel="dff", module="dff_cocotb")


if __name__ == "__main__":
    test_dff()
