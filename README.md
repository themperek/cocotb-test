# cocotb-test
[![Build Status](https://dev.azure.com/themperek/themperek/_apis/build/status/themperek.cocotb-test?branchName=master)](https://dev.azure.com/themperek/themperek/_build/latest?definitionId=2&branchName=master)

``cocotb-test`` provides standard python unit testing capabilities for [cocotb](https://github.com/potentialventures/cocotb)
- allow the look and feal of python unit testing
- remove the need for Makefiles
- allow easy customization of simulation flow
- in future allow to use [pytest-xdist](https://pypi.org/project/pytest-xdist/) for parallel runs

**!Proof of Concept!**

# Usage:

- Install and use [conda](https://conda.io/miniconda.html) for python (can be installed in user/local folder).

- Install development tools for conda (Windows only):
```bash
conda install --yes m2w64-gcc libpython
```

- Install the package via [pip](https://pip.pypa.io/en/stable/user_guide/):
```bash
pip install https://github.com/themperek/cocotb-test/archive/master.zip
```
&emsp;or
```bash
git clone https://github.com/themperek/cocotb-test.git
pip install -e cocotb-test
```

- Create a `test_dff.py` file (check [test folder](https://github.com/themperek/cocotb-test/tree/master/tests) for more):
```python
from cocotb_test.run import run
def test_dff():
    run(
        verilog_sources=['dff.v'], # sources
        toplevel='dff',            # top level HDL
        module='dff_cocotb'        # name of cocotb test module
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
SIM=icarus pytest -s --junitxml=test-results.xml tests
```
