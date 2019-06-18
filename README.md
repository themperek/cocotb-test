# cocotb-test
Unit testing for cocotb

**!Prof of concept!**

# Usage:
Install:
```bash
pip install -e .
```


In the `test_*` file with cocotb tests defined:
```python
from cocotb_test.run import Run
def test_run():
    Run(sources=['dff.v'], toplevel='dff')

if __name__ == "__main__":
    test_run()
```

Run: 
```bash
pytest -s
```


