from cocotb_test.simulator import run
import pytest
import os

dir = os.path.dirname(__file__)

@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
@pytest.mark.xfail(reason="Expected to fail with no work_dir specified")
def test_dff_no_workdir():
    run(verilog_sources=[os.path.join(dir, "..", "..", "dff.sv")], toplevel="dff_test", module="dff_cocotb")  # sources  # top level HDL  # name of cocotb test module

@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not suported")
def test_dff_workdir():
    run(verilog_sources=[os.path.join(dir, "..", "..", "dff.sv")], work_dir=os.path.join(dir, "..", ".."), toplevel="dff_test", module="dff_cocotb")  # sources  # top level HDL  # name of cocotb test module


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