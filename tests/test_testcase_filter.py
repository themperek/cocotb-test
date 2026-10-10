import os

import pytest

from cocotb_test.simulator import run

tests_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not supported")
def test_testcase_matches_exact_name_only():
    # testcase="test_soak" must not select test_soak_extended by substring
    # under cocotb 2.x COCOTB_TEST_FILTER matching (themperek/cocotb-test#285).
    run(
        verilog_sources=[os.path.join(tests_dir, "dff.sv")],
        toplevel="dff_test",
        module="testcase_cocotb",
        testcase="test_soak",
        sim_build="sim_build/testcase_filter_exact_name",
    )


@pytest.mark.skipif(os.getenv("SIM") in ("ghdl", "nvc"), reason="Verilog not supported")
def test_testcase_comma_separated_names():
    # Comma-separated names keep working as they did with the cocotb 1.x
    # TESTCASE variable; test_soak_extended must still not run.
    run(
        verilog_sources=[os.path.join(tests_dir, "dff.sv")],
        toplevel="dff_test",
        module="testcase_cocotb",
        testcase="test_soak,test_other",
        sim_build="sim_build/testcase_filter_name_list",
    )
