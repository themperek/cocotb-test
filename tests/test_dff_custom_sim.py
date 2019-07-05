from cocotb_test.run import run
from cocotb_test.simulator import Icarus, Ius
import pytest
import os


class IcarusCustom(Icarus):
    def run_command(self):
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


@pytest.fixture(scope="module", autouse=True)
def module_run_at_beginning(request):
    print('\n\nIn module_run_at_beginning()\n\n')

    def module_run_at_end():
            print('\n\nIn module_run_at_end()\n\n')
    request.addfinalizer(module_run_at_end)


@pytest.mark.skipif(os.getenv("SIM") != "icarus", reason="Custom for Icarus")
def test_dff_custom_icarus():
    run(
        simulator=IcarusCustom,
        verilog_sources=["dff.v"],
        toplevel="dff",
        python_search=["."],
        module="dff_cocotb",
        logfile="custom_log.log",  # extra custom argument
    )


class IusCustom(Ius):
    def build_command(self):
        cmd = (
            [
                "xrun",
                "-loadvpi",
                os.path.join(self.lib_dir, "libvpi." + self.lib_ext)
                + ":vlog_startup_routines_bootstrap",
                "-plinowarn",
                "-access", "+rwc",
                "-f", self.defsfile,
            ]
        )

        return [cmd]


@pytest.mark.skipif(os.getenv("SIM") != "ius", reason="Custom for IUS")
def test_dff_custom_ius():
    run(
        simulator=IusCustom,
        toplevel="dff",
        python_search=["."],
        module="dff_cocotb",
        defsfile="ius_defines.f",  # extra custom argument
    )


if __name__ == "__main__":
    test_dff_custom()
