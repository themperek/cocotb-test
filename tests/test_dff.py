from cocotb_test.run import run


def test_dff():
    run(
        verilog_sources=["dff.v"],  # sources
        toplevel="dff",             # top level HDL
        module="dff_cocotb",        # name of cocotb test module
    )


if __name__ == "__main__":
    test_dff()
