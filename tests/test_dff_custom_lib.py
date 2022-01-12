from cocotb_test.simulator import run
import pytest
import os

tests_dir = os.path.dirname(__file__)

@pytest.mark.skipif(os.getenv("SIM") != "questa", reason="Named libraries only supported for Questa simulator")
def test_dff_vhdl():
    run(
        vhdl_sources = {
            "some_lib": [os.path.join(tests_dir, "dff.vhdl")],
            "some_other_lib": [os.path.join(tests_dir, "dff_wrapper.vhdl")],
        },
        toplevel="dff_wrapper",
        module="dff_cocotb",
        toplevel_lang="vhdl",
        toplevel_lib="some_other_lib",
        vhdl_compile_args=["-2008"],
        force_compile=True,
    )


if __name__ == "__main__":
    test_dff_vhdl()