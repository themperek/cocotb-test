# cocotb-test
Unit testing for cocotb. Remove need for Makefiles. The goal is also to use [pytest-xdist](https://pypi.org/project/pytest-xdist/) for parallel run.

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
        python_search=['.'],       # serch path for cocotb test module
        module='dff_cocotb'        # name of cocotb test module
    )
```

Run [pytest](https://docs.pytest.org/en/latest/contents.html): 
```bash
pytest -s
```
