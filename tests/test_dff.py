from cocotb_test.run import run
from cocotb_test.simulator import Icarus


def test_dff():
    run(
        verilog_sources=['dff.v'], # sources
        toplevel='dff',            # top level HDL
        python_search=['.'],       # search path for cocotb test module
        module='dff_cocotb',        # name of cocotb test module
        #simulator=Icarus
    )

if __name__ == "__main__":
    test_dff()
