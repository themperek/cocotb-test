
from cocotb_test.run import Run

def test_dff():
    Run(
        verilog_sources=['dff.v'], # sources
        toplevel='dff',            # top level HDL
        python_search=['.'],       # serch path for cocotb test module
        module='dff_cocotb'        # name of cocotb test module
    )

if __name__ == "__main__":
    test_dff()

