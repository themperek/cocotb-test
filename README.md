# cocotb-test
[![Build Status](https://dev.azure.com/themperek/themperek/_apis/build/status/themperek.cocotb-test?branchName=master)](https://dev.azure.com/themperek/themperek/_build/latest?definitionId=2&branchName=master)

Unit testing for [cocotb](https://github.com/potentialventures/cocotb). Remove need for Makefiles. The goal is also to use [pytest-xdist](https://pypi.org/project/pytest-xdist/) for parallel run.

**!Proof of Concept!**

# Usage:

Install via [pip](https://pip.pypa.io/en/stable/user_guide/):
```bash
pip install -e .
```

Create `test_*` file:
```python
from cocotb_test.run import Run
def test_dff():
    Run(
        verilog_sources=['dff.v'], # sources
        toplevel='dff',            # top level HDL
        python_search=['.'],       # search path for cocotb test module
        module='dff_cocotb'        # name of cocotb test module
    )
```

Run [pytest](https://docs.pytest.org/en/latest/contents.html): 
```bash
pytest -s
```
