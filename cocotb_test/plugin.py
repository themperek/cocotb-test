import os
import shutil
from xml.etree import cElementTree as ET


class ResultsCocotb(object):
    def __init__(self, results_xml_output):
        self.results_xml_output = results_xml_output
        self.names = []
        self.results_xml_dir = os.path.abspath(".cocotb-results")

    def get_results_xml_file(self, nodeid):
        return os.path.join(self.results_xml_dir, nodeid.replace(os.sep, "_").replace("/", "_").replace(":", "-") + ".xml")

    def pytest_runtest_logreport(self, report):
        if report.when == "call" and report.outcome != "skipped":
            self.names.append(report.nodeid)

    def pytest_sessionstart(self, session):
        os.makedirs(self.results_xml_dir, exist_ok=True)

    def pytest_runtest_setup(self, item):

        cocotb_result_file = self.get_results_xml_file(item._nodeid)
        if os.path.exists(cocotb_result_file):
            os.remove(cocotb_result_file)

        os.environ["COCOTB_RESULTS_FILE"] = self.get_results_xml_file(item._nodeid)
        os.environ["RESULT_TESTPACKAGE"] = item._nodeid

    def pytest_sessionfinish(self, session):

        result = ET.Element("testsuites", name="results")

        for nodeid in self.names:
            fname = self.get_results_xml_file(nodeid)

            if os.path.isfile(fname):
                tree = ET.parse(fname)
                for testsuite in tree.iter("testsuite"):
                    use_element = None

                    for testcase in testsuite.iter("testcase"):
                        testcase.set("classname", "cocotb." + testcase.get("classname"))  # add cocotb. for easier selection

                    for existing in result:
                        if existing.get("name") == testsuite.get("name") and (existing.get("package") == testsuite.get("package")):
                            use_element = existing
                            break
                    if use_element is None:
                        result.append(testsuite)
                    else:
                        use_element.extend(list(testsuite))

        ET.ElementTree(result).write(self.results_xml_output, encoding="UTF-8")

    def pytest_runtest_teardown(self, item, nextitem):
        results_xml_file = self.get_results_xml_file(item._nodeid)
        results_xml_file_defulat = os.path.join("sim_build", "results.xml")

        if os.path.isfile(results_xml_file_defulat):
            os.rename(results_xml_file_defulat, results_xml_file)


def pytest_unconfigure(config):
    cocotb = getattr(config, "_cocotb", None)
    if cocotb:
        config.pluginmanager.unregister(cocotb)


def pytest_configure(config):
    if config.option.cocotb_xml:
        config._cocotb = ResultsCocotb(config.option.cocotb_xml)
        config.pluginmanager.register(config._cocotb)


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting")
    group.addoption(
        "--cocotbxml",
        "--cocotb-xml",
        action="store",
        dest="cocotb_xml",
        default=None,
        metavar="path",
        help="create junit-xml style report file for cocotb reports at given path.",
    )
