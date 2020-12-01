"""Test cli"""
import pytest

from conftest import acid


def test_version(acid_installed):
    """acid version"""
    assert acid(["version"])

    if acid_installed:
        assert acid(["version"], cmd="acid")


def test_no_action():
    """acid images"""
    acid([], except_fail=True)


def test_installed(acid_installed):
    """Test if acid command is installed"""
    if not acid_installed:
        pytest.skip("Acid not installed")
    assert acid(["version"], cmd="acid")


def test_images():
    """acid images"""
    assert "centos_8" in acid(["images", "awsEc2"]).stdout.splitlines()
    assert "centos_8" in acid(["images", "azureVm"]).stdout.splitlines()
    acid(["images", "not_exists"], except_fail=True)
    acid(["images"], except_fail=True)


def test_no_agent_list(tmp_user_dir):
    """acid list (No agent)"""
    assert acid(["list"]).stdout.strip() == ""


def test_no_agent_show(tmp_user_dir):
    """acid show (No agent)"""
    acid(["show"], except_fail=True)
    acid(["show", "-a", "Agent"], except_fail=True)


def test_no_agent_start(tmp_user_dir):
    """acid stop (No agent)"""
    acid(["start", "-a", "Agent", "-i", "not_exists"], except_fail=True)
    acid(
        ["start", "-a", "Agent", "--ansiblePlaybook", "not_exists.yml"],
        except_fail=True,
    )
    acid(
        ["start", "-a", "Agent", "--ansiblePlaybook", "not_exists.yml"],
        except_fail=True,
        debug=False,
    )


def test_no_agent_ssh(tmp_user_dir):
    """acid ssh (No agent)"""
    acid(["ssh"], except_fail=True)
    acid(["ssh", "-a", "Agent"], except_fail=True)


def test_no_agent_stop(tmp_user_dir):
    """acid stop (No agent)"""
    acid(["stop", "-f"], except_fail=True)
    acid(["stop", "-a", "not_exists", "-f"], except_fail=True)


def test_images_completer():
    """Test yaml completer"""
    from acidcli import _Command
    from argparse import Namespace

    cmd = _Command(["images", "awsEc2"])
    centos_images = list(cmd._images_completer("cent", Namespace(provider="awsEc2")))
    ubuntu = "ubuntu_20_04"
    assert "centos_8" in centos_images
    assert ubuntu not in centos_images
    assert ubuntu in list(cmd._images_completer("ub", Namespace(provider="awsEc2")))
    assert cmd._images_completer("", Namespace(provider=None)) is None


def test_agent():
    """acid start & stop"""
    check_connection = [
        "--",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "exit 0",
    ]
    try:
        # Test create an agent
        acid(["start", "-t", "t3a.nano", "-a", "agent1"])
        assert acid(["list"]).stdout.strip()
        assert acid(["show", "-a", "agent1"])
        acid(
            [
                "ssh",
                "-a",
                "agent1",
            ]
            + check_connection
        )

        # Test try to create already existing agent
        acid(["start", "-a", "agent1"], except_fail=True)

        # Test create another agent
        try:
            acid(
                [
                    "start",
                    "-t",
                    "t3a.nano",
                    "-a",
                    "agent2",
                    "--ansiblePlaybook",
                    "tests/playbook.yml",
                    "--ansibleRequirements",
                    "tests/requirements.yml",
                    "--update",
                ]
            )
            assert acid(["list"]).stdout.strip()
            assert acid(["show", "-a", "agent2"])
            acid(
                [
                    "ssh",
                    "-a",
                    "agent2",
                ]
                + check_connection
            )

            # Test passing "-i" ssh arg
            acid(["ssh", "-a", "agent2", "--", "-i", "key.pem"], except_fail=True)

            # Test stop with cancel
            acid(["stop", "-a", "agent2"], stdin="n\n")

        finally:
            acid(["stop", "-a", "agent2"], stdin="y\n")

    finally:
        for agent in acid(["list"]).stdout.strip().splitlines():
            acid(["stop", "-a", agent, "-f"])
