
from packaging.version import parse as parse_version
import cocotb

# Use 1.999.0 in comparison to match pre-release versions of cocotb too
cocotb_2x_or_newer = parse_version(cocotb.__version__) > parse_version("1.999.0")

if cocotb_2x_or_newer:
    import cocotb_tools.config as cocotb_config
else:
    import cocotb.config as cocotb_config
