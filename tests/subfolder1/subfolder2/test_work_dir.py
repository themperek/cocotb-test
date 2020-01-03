from cocotb_test.run import run
import pytest
import os


@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
@pytest.mark.xfail(reason="Expected to fail with no work_dir specified")
def test_dff_no_workdir():
    run(verilog_sources=["../../dff.v"], toplevel="dff_test", module="dff_cocotb")  # sources  # top level HDL  # name of cocotb test module

@pytest.mark.skipif(os.getenv("SIM") == "ghdl", reason="Verilog not suported")
def test_dff_workdir():
    run(verilog_sources=["../../dff.v"], work_dir="../../", toplevel="dff_test", module="dff_cocotb")  # sources  # top level HDL  # name of cocotb test module


if __name__ == "__main__":
    # Intended to be run via pytest, not directly
    for test in [test_dff_no_workdir, test_dff_workdir]:
        try:
            test()
        except:
            if test == test_dff_no_workdir:
                print("\n**** Expected failure when no work_dir is set.\n")
            else:
                raise