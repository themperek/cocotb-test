# cocotb-test
[![Build Status](https://dev.azure.com/themperek/themperek/_apis/build/status/themperek.cocotb-test?branchName=master)](https://dev.azure.com/themperek/themperek/_build/latest?definitionId=2&branchName=master)
[![PyPI version](https://badge.fury.io/py/cocotb-test.svg)](https://badge.fury.io/py/cocotb-test)

``cocotb-test`` provides standard python unit testing capabilities for [cocotb](https://github.com/cocotb/cocotb)
- allow the look and feel of Python unit testing
- remove the need for Makefiles (includes Makefile compatibility mode)
- allow easy customization of simulation flow
- allow to use [pytest-xdist](https://pypi.org/project/pytest-xdist/) or [pytest-parallel](https://github.com/browsertron/pytest-parallel) for parallel runs

# Usage:

- Install [cocotb](https://docs.cocotb.org/).

- Install simulator (for Icarus Verilog with conda):
```bash
conda install -c conda-forge iverilog
```
- Install the package via [pip](https://pip.pypa.io/en/stable/user_guide/):
```bash
pip install cocotb-test
```
&emsp;or development version
```bash
pip install -v https://github.com/themperek/cocotb-test/archive/master.zip
```
&emsp;or
```bash
git clone https://github.com/themperek/cocotb-test.git
pip install -v -e cocotb-test
```

- Create a `test_dff.py` file (check [test folder](https://github.com/themperek/cocotb-test/tree/master/tests) for more examples):
```python
from cocotb_test.simulator import run
def test_dff():
    run(
        verilog_sources=["dff.v"], # sources
        toplevel="dff",            # top level HDL
        module="dff_cocotb"        # name of cocotb test module
    )
```

- Run [pytest](https://docs.pytest.org/en/latest/contents.html): 
```bash
pytest -o log_cli=True
```

# Running (some) tests and examples from cocotb
For cocotb tests/examples install cocotb in editable mode  
```bash
git clone https://github.com/potentialventures/cocotb.git
pip install -e cocotb
SIM=icarus pytest -o log_cli=True --junitxml=test-results.xml --cocotbxml=test-cocotb.xml tests
```

# Related resources
- [pytest logging](https://docs.pytest.org/en/stable/logging.html) - pytest logging documentation 
- [pytest-xdist](https://pypi.org/project/pytest-xdist/) - test run parallelization (see [test_parallel](https://github.com/themperek/cocotb-test/blob/master/tests/test_parallel.py))
- [pytest-parallel](https://github.com/browsertron/pytest-parallel) - parallel and concurrent testing  (see [test_parallel](https://github.com/themperek/cocotb-test/blob/master/tests/test_parallel.py))
- [pytest-html](https://github.com/pytest-dev/pytest-html) - generates a HTML report for the test results
- [pytest-sugar](https://github.com/Teemu/pytest-sugar/) - sugar
