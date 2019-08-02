import os
import sys
import inspect
import shutil
import tempfile

import cocotb_test.simulator
from cocotb_test.build_libs import build_libs

from xml.etree import cElementTree as ET


def run(simulator=None, **kwargs):

    supported_sim = ["icarus", "questa", "ius", "vcs", "ghdl"]
    if (os.getenv("SIM") in supported_sim) or simulator:
        pass
    else:
        raise NotImplementedError("Set SIM variable. Supported: " + ", ".join(supported_sim))

    run_filename = inspect.getframeinfo(inspect.currentframe().f_back)[0]
    kwargs["run_filename"] = run_filename

    if simulator:
        sim = simulator(**kwargs)
    elif os.getenv("SIM") == "icarus":
        sim = cocotb_test.simulator.Icarus(**kwargs)
    elif os.getenv("SIM") == "questa":
        sim = cocotb_test.simulator.Questa(**kwargs)
    elif os.getenv("SIM") == "ius":
        sim = cocotb_test.simulator.Ius(**kwargs)
    elif os.getenv("SIM") == "vcs":
        sim = cocotb_test.simulator.Vcs(**kwargs)
    elif os.getenv("SIM") == "ghdl":
        sim = cocotb_test.simulator.Ghdl(**kwargs)

    results_xml_file_defulat = os.path.join(sim.sim_dir, "results.xml")
    if os.path.isfile(results_xml_file_defulat):
        os.remove(results_xml_file_defulat)

    fo = tempfile.NamedTemporaryFile()
    results_xml_file = fo.name
    fo.close()
    os.environ["COCOTB_RESULTS_FILE_NAME"] = results_xml_file

    sim.run()

    # HACK: for compatibility to be removed
    if os.path.isfile(results_xml_file_defulat):
        results_xml_file = results_xml_file_defulat
    assert os.path.isfile(results_xml_file), "Simulation terminated abnormally. Results file not found."

    tree = ET.parse(results_xml_file)
    for ts in tree.iter("testsuite"):
        for tc in ts.iter("testcase"):
            for failure in tc.iter("failure"):
                assert False, '{} class="{}" test="{}" error={}'.format(failure.get("message"), tc.get("classname"), tc.get("name"), failure.get("stdout"))

    return results_xml_file


def clean(recursive=False, all=False):
    dir = os.getcwd()

    def rm_clean():
        sim_build_dir = os.path.join(dir, "sim_build")
        if os.path.isdir(sim_build_dir):
            print("Removing:", sim_build_dir)
            shutil.rmtree(sim_build_dir, ignore_errors=True)
            if all:
                libs_build_dir = os.path.join(dir, "cocotb_build")
                if os.path.isdir(libs_build_dir):
                    print("Removing:", libs_build_dir)
                    shutil.rmtree(libs_build_dir, ignore_errors=True)

    rm_clean()

    if recursive:
        for dir, subFolders, files in os.walk(dir):
            rm_clean()
