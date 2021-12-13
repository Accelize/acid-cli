"""Pytest configuration"""
import pytest
from subprocess import run, TimeoutExpired
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


def acid(
    args,
    except_fail=False,
    cmd=None,
    debug=True,
    stdin=None,
    capture_output=True,
    timeout=600,
    ignore_outcome=False,
):
    """
    Run acid.

    Args:
        args (list of str): Acid arguments.
        cmd (str): Acid command to use.
        except_fail (bool): If True, pass tests if command fail. Default to fail test
            if command fail.
        debug (bool): If True, enable Acid debug mode that increase verbosity.
        stdin (str): If specified, send string over standard input.
        capture_output (bool): if True, capture output.
        timeout (int): Command timeout in seconds.
        ignore_outcome (bool): If True, ignore return code.

    Returns:
        subprocess.CompletedProcess: Result
    """
    command = [CMD if cmd is None else cmd]
    if debug:
        command.append("--debug")
    try:
        process = run(
            command + args,
            capture_output=capture_output,
            universal_newlines=True,
            input=stdin,
            timeout=timeout,
        )
    except TimeoutExpired as exception:
        return pytest.fail(
            f'Timeout on "{" ".join(["acid"] + args)}" after {exception.args[1]:.0f}s'
        )

    if ignore_outcome:
        return process

    returncode = process.returncode
    if (returncode and not except_fail) or (except_fail and not returncode):
        if capture_output:
            stdout = process.stdout.strip()
            if stdout:
                stdout = f"STDOUT:\n{stdout}"
            stderr = process.stderr.strip()
            if stderr:
                stderr = f"STDERR:\n{stderr}"
        else:
            stdout = stderr = None
        pytest.fail(
            f"\n\nCOMMAND:\n{' '.join(['acid'] + args)}\n\n"
            + "\n\n".join(out for out in (stdout, stderr) if out)
        )
    return process


@pytest.fixture(scope="session")
def tmp_user_dir(tmpdir_factory):
    """Ensure acid use a temporary user directory"""
    if "ACID_USER_DIR" not in environ:
        environ["ACID_USER_DIR"] = str(tmpdir_factory.mktemp("acid"))
