"""Pytest configuration"""
import pytest
from subprocess import run
from os import environ
from os.path import dirname, join
import sys

sys.path.append(dirname(dirname(__file__)))
CMD = join(dirname(dirname(__file__)), "acidcli/__init__.py")
environ["COVERAGE_PROCESS_START"] = ""


def pytest_addoption(parser):
    """
    Add command lines arguments
    """
    parser.addoption(
        "--installed",
        action="store_true",
        help="If specified, check if Acid command is installed",
    )


@pytest.fixture
def acid_installed(request):
    """
    Acid is installed.

    Args:
        request: Pytest request.

    Returns:
        bool: Acid installed
    """
    return request.config.getoption("--installed")


def acid(args, except_fail=False, cmd=None, debug=True, stdin=None):
    """
    Run acid.

    Args:
        args (list of str): Acid arguments.
        cmd (str): Acid command to use.
        except_fail (bool): If True, pass tests if command fail. Default to fail test
            if command fail.
        debug (bool): If True, enable Acid debug mode that increase verbosity.
        stdin (str): If specified, send string over standard input.

    Returns:
        subprocess.CompletedProcess: Result
    """
    command = [CMD if cmd is None else cmd]
    if debug:
        command.append("--debug")
    process = run(
        command + args, capture_output=True, universal_newlines=True, input=stdin
    )
    returncode = process.returncode
    if (returncode and not except_fail) or (except_fail and not returncode):
        stdout = process.stdout.strip()
        full_cmd = " ".join(["acid"] + args)
        if stdout:
            stdout = f"STDOUT:\n{stdout}"
        stderr = process.stderr.strip()
        if stderr:
            stderr = f"STDERR:\n{stderr}"
        pytest.fail(
            f"\n\nCOMMAND:\n{full_cmd}\n\n"
            + "\n\n".join(out for out in (stdout, stderr) if out)
        )
    return process


@pytest.fixture(scope="session")
def tmp_user_dir(tmpdir_factory):
    """Ensure acid use a temporary user directory"""
    environ["ACID_USER_DIR"] = str(tmpdir_factory.mktemp("acid"))
