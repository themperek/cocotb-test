from cocotb_test.run import run
from cocotb_test.simulator import Icarus
import pytest
import os


class IcarusCustom(Icarus):
    def run_commnd(self):
        return [
            "vvp",
            "-v",
            "-l",
            self.logfile,
            "-M",
            self.lib_dir,
            "-m",
            "gpivpi",
            self.sim_file,
        ]


@pytest.mark.skipif(os.environ["SIM"] != "icarus", reason="Custom for Icarus")
def test_dff_custom():
    run(
        simulator=IcarusCustom,
        verilog_sources=["dff.v"],
        toplevel="dff",
        python_search=["."],
        module="dff_cocotb",
        logfile="custom_log.log",  # extra custom argument
    )


if __name__ == "__main__":
    test_dff_custom()
