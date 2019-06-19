# cocotb-test
Unit testing for cocotb

**!Proof of Concept!**

# Usage:
For this to work [cocotb](https://github.com/potentialventures/cocotb)  neend this patch: https://github.com/potentialventures/cocotb/pull/956

Install via [pip](https://pip.pypa.io/en/stable/user_guide/):
```bash
pip install -e .
```


In the `test_*` file with [cocotb](https://github.com/potentialventures/cocotb) tests defined:
```python
from cocotb_test.run import Run
def test_run():
    Run(sources=['dff.v'], toplevel='dff')

if __name__ == "__main__":
    test_run()
```

Run [pytest](https://docs.pytest.org/en/latest/contents.html): 
```bash
pytest -s
```


