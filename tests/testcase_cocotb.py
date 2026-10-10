# Cocotb test module for the testcase= exact-name selection regression tests
# (tests/test_testcase_filter.py). test_soak_extended exists to prove that
# testcase="test_soak" does not select it by substring under cocotb 2.x
# COCOTB_TEST_FILTER matching.

import cocotb


@cocotb.test()
async def test_soak(dut):
    pass


@cocotb.test()
async def test_soak_extended(dut):
    raise AssertionError("selected by substring match; testcase= must be anchored")


@cocotb.test()
async def test_other(dut):
    pass
