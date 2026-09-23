import os
import sys

import nox

COCOTB_VERSIONS = ["v1.9.2", "v2.0.1", "v2.1.0"]
COCOTB_REPO = "https://github.com/cocotb/cocotb.git"

nox.options.sessions = ["tests"]
nox.options.default_venv_backend = "venv"


def _install_cocotb(session, version):
    # Editable install from a git clone: tests need cocotb's examples/ and tests/ directories.
    src = os.path.join(session.cache_dir, "cocotb", version)
    if not os.path.isdir(src):
        session.run(
            "git", "clone", "--depth=1", "--branch", version, COCOTB_REPO, src,
            external=True,
        )
    if version.startswith(("v1.", "v2.0.")):
        # These builds pass `dry_run` to copy_file(), removed in newer setuptools.
        session.install("setuptools<80", "wheel")
        session.install("--no-build-isolation", "-e", src)
    else:
        session.install("-e", src)


@nox.session
@nox.parametrize("cocotb", COCOTB_VERSIONS)
def tests(session, cocotb):
    sim = os.environ.get("SIM", "icarus")
    session.env["SIM"] = sim
    on_windows = sys.platform == "win32"

    _install_cocotb(session, cocotb)
    session.install(".", "pytest", "pytest-xdist")

    session.run("pytest", "-s", "tests/test_dff.py")

    if sim != "verilator":
        session.run(
            "pytest", "--junitxml=test-results.xml", "--cocotbxml=test-cocotb.xml", "tests"
        )

    if not on_windows:
        session.run("pytest", "-m", "compile", "tests/test_parallel.py")
        session.run(
            "pytest", "-m", "not compile", "-n", "2", "--cocotbxml=test-cocotb.xml",
            "tests/test_parallel.py",
        )

    if sys.platform.startswith("linux") and sim == "icarus":
        session.run("make", "-C", "tests", external=True)

    # pytest-parallel is unmaintained and needs pytest<7.2 ("module 'py' has no attribute 'log'"),
    # which does not work on newer Pythons. Runs last because it downgrades pytest.
    if not on_windows and _python_version(session) < (3, 12):
        session.install("pytest-parallel", "pytest==7.1")
        session.run("pytest", "-m", "compile", "tests/test_parallel.py")
        session.run("pytest", "-m", "not compile", "--workers", "2", "tests/test_parallel.py")


def _python_version(session):
    out = session.run(
        "python", "-c", "import sys; print(*sys.version_info[:2])", silent=True
    )
    return tuple(int(v) for v in out.split())
