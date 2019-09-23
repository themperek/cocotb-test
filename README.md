# cocotb-test
[![Build Status](https://dev.azure.com/themperek/themperek/_apis/build/status/themperek.cocotb-test?branchName=master)](https://dev.azure.com/themperek/themperek/_build/latest?definitionId=2&branchName=master)
[![PyPI version](https://badge.fury.io/py/cocotb-test.svg)](https://badge.fury.io/py/cocotb-test)

``cocotb-test`` provides standard python unit testing capabilities for [cocotb](https://github.com/cocotb/cocotb)
- allow the look and feel of Python unit testing
- remove the need for Makefiles (includes Makefile compatibility mode)
- allow easy customization of simulation flow
- easy installation (especially on Windows)
- allow to use [pytest-xdist](https://pypi.org/project/pytest-xdist/) for parallel runs (need [#1053](https://github.com/cocotb/cocotb/pull/1053) )

# **!Proof of Concept!**

# Usage:

- Install and use [conda](https://conda.io/miniconda.html) for Python (can be installed in user/local folder).

- Install development tools for conda (Windows only):
```bash
conda install --yes m2w64-gcc libpython
```
- Install simulator (for Icarus Verilog):
```bash
conda install --yes -c conda-forge iverilog
```
- Install the package via [pip](https://pip.pypa.io/en/stable/user_guide/):
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
from cocotb_test.run import run
def test_dff():
    run(
        verilog_sources=["dff.v"], # sources
        toplevel="dff",            # top level HDL
        module="dff_cocotb"        # name of cocotb test module
    )
```

- Run [pytest](https://docs.pytest.org/en/latest/contents.html): 
```bash
pytest -s 
```

# Running (some) tests and examples from cocotb
For cocotb tests/examples install cocotb in editable mode  
```bash
git clone https://github.com/potentialventures/cocotb.git
pip install -e cocotb
SIM=icarus pytest -s --junitxml=test-results.xml --cocotbxml=test-cocotb.xml tests
```
