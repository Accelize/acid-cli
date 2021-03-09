#! /usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""
Acid CLI entry point
"""
import sys as _sys
import os as _os

_DIR = _os.path.dirname(_os.path.realpath(__file__))
_ACID_DIR = _os.path.join(_DIR, "acid")
_AGENTS_SRC = _os.path.join(_ACID_DIR, "agents")
USER_DIR = _os.getenv("ACID_USER_DIR", _os.path.expanduser("~/.config/acid"))
AGENTS_DIR = _os.path.join(USER_DIR, "agents")
_TF = _os.path.join(USER_DIR, "lib/terraform")
_TF_PLUGINS = _os.path.join(_TF, "plugins")
_ANSIBLE_ROLES = _os.path.join(USER_DIR, "lib/ansible/roles")


class _Command:
    """Available actions"""

    def __init__(self, args=None):
        from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, REMAINDER
        from argcomplete import autocomplete
        from argcomplete.completers import ChoicesCompleter

        parser = ArgumentParser(prog="acid", description="Acid CLI")
        sub_parsers = parser.add_subparsers(
            dest="parser_action", title="Commands", help="Commands", description=""
        )
        parser.add_argument(
            "--debug",
            "-d",
            action="store_true",
            help="If True, show full error traceback.",
        )

        _os.makedirs(AGENTS_DIR, exist_ok=True)
        _os.chmod(AGENTS_DIR, 0o700)
        agents_exists = tuple(
            name
            for name in _os.listdir(AGENTS_DIR)
            if _os.path.isdir(_os.path.join(AGENTS_DIR, name))
        )
        agents_exists_completer = ChoicesCompleter(agents_exists)
        providers = tuple(
            name
            for name in _os.listdir(_AGENTS_SRC)
            if _os.path.isdir(_os.path.join(_AGENTS_SRC, name))
        )
        providers_completer = ChoicesCompleter(providers)
        if len(agents_exists) == 1:
            agent_default = agents_exists[0]
        else:
            agent_default = None
        agent_load_args = dict(default=agent_default, required=agent_default is None)
        bool_choices = ("true", "false")
        bool_completer = ChoicesCompleter(bool_choices)

        description = "Start a new agent."
        action = sub_parsers.add_parser(
            "start",
            help=description,
            description=description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        action.add_argument(
            "--agentDescription",
            "-a",
            default="Agent",
            help="Agent description, used to identify agent in the future.",
        )
        action.add_argument(
            "--agentPool",
            "-P",
            help="Azure Pipeline Agent pool name. Can also be set with "
            '"AZURE_AGENT_POOL" environment variable.',
            default="Default",
        )
        action.add_argument(
            "--agentOrganizationUrl",
            "-o",
            help="Azure Pipeline organization URL "
            "(https://dev.azure.com/ORGANIZATION_NAME/). "
            "The agent will not be registered in Azure Pipeline if missing. "
            'Can also be set with "AZURE_AGENT_URL" environment variable.',
        )
        action.add_argument(
            "--agentManagerToken",
            "-m",
            help="Azure Personal Access Token to use to configure agent. "
            "The agent will not be registered in Azure Pipeline if missing. "
            'Can also be set with "AZURE_AGENT_TOKEN" environment variable.',
        )
        action.add_argument(
            "--agentVersion",
            help="Azure Pipeline agent version to use. Default to the latest version.",
        )
        action.add_argument(
            "--agentEnv",
            help="Azure Pipeline agent environment variables as a JSON formatted "
            "string.",
            default='{"AZP_AGENT_USE_LEGACY_HTTP": "true"}',
        )
        action.add_argument(
            "--provider",
            "-p",
            help="Agent instance provider.",
            default="awsEc2",
            choices=providers,
        ).completer = providers_completer
        action.add_argument("--instanceType", "-t", help="Agent instance type.")
        action.add_argument(
            "--volumeSize",
            "-s",
            type=int,
            help="Root volume size in GB. Default to size specified by the image",
        )
        action.add_argument(
            "--image", "-i", help="Image name to use."
        ).completer = self._images_completer
        action.add_argument(
            "--ansiblePlaybook",
            "-A",
            help='Path to the Ansible "playbook.yml" file used to provision the agent.',
            default=(
                "playbook.yml"
                if _os.path.isfile("playbook.yml")
                else _os.path.join(_AGENTS_SRC, "playbook.yml")
            ),
        )
        action.add_argument(
            "--ansibleRequirements",
            "-R",
            help='Path to Ansible "requirements.yml" file used to define roles to '
            "install",
            default=(
                "requirements.yml" if _os.path.isfile("requirements.yml") else None
            ),
        )
        action.add_argument(
            "--timeout",
            "-T",
            help="Agent shutdown timeout in minute. "
            "If not specified, the agent will run infinitely.",
            type=int,
        )
        action.add_argument(
            "--spot",
            help="Use spot instance",
            choices=bool_choices,
        ).completer = bool_completer
        action.add_argument(
            "--inMemoryWorkDir",
            help='If "true", the agent work directory and "/tmp" are mounted in memory '
            "(tmpfs)",
            choices=bool_choices,
        ).completer = bool_completer
        action.add_argument(
            "--region",
            help="Cloud provider region",
        )
        action.add_argument(
            "--resourceGroupName",
            help="Resource group name (azureVm only)",
        )
        action.add_argument(
            "--virtualNetworkName",
            help="Virtual network name (azureVm only)",
        )
        action.add_argument(
            "--update",
            "-u",
            action="store_true",
            help="If True, update Ansible roles, Terraform and its plugins.",
        )
        description = "Stop and destroy the agent."
        action = sub_parsers.add_parser(
            "stop",
            help=description,
            description=description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        action.add_argument(
            "--agentDescription",
            "-a",
            help="Agent description, used to select agent to stop.",
            **agent_load_args,
        ).completer = agents_exists_completer
        action.add_argument(
            "--force",
            "-f",
            help="Force agent destruction without confirmation.",
            action="store_true",
        )
        description = "Connect to the agent using SSH."
        action = sub_parsers.add_parser(
            "ssh",
            help=description,
            description=description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        action.add_argument(
            "--agentDescription",
            "-a",
            help="Agent description, used to select agent to SSH.",
            **agent_load_args,
        ).completer = agents_exists_completer
        action.add_argument(
            "ssh_args",
            nargs=REMAINDER,
            help='SSH command arguments after "--".',
        )
        description = "List existing agents."
        sub_parsers.add_parser(
            "list",
            help=description,
            description=description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        description = "Show the agent parameters."
        action = sub_parsers.add_parser(
            "show",
            help=description,
            description=description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        action.add_argument(
            "--agentDescription",
            "-a",
            help="Agent description, used to select agent to show.",
            **agent_load_args,
        ).completer = agents_exists_completer
        description = "List available images for a provider."
        action = sub_parsers.add_parser(
            "images",
            help=description,
            description=description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        action.add_argument(
            "provider",
            help="Agent instance provider.",
            choices=providers,
        ).completer = providers_completer
        description = "Show version."
        sub_parsers.add_parser(
            "version",
            help=description,
            description=description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )

        autocomplete(parser)
        self._params = params = vars(parser.parse_args(args))
        parser_action = params.pop("parser_action")
        self._debug = params.pop("debug", False)
        self._force_update = params.pop("update", False)
        self._agent = params.get("agentDescription")
        self._terraform_path = None

        try:
            self._agent_dir = _os.path.join(AGENTS_DIR, self._agent)
        except TypeError:
            self._agent_dir = None

        if parser_action == "start":
            if _os.path.isdir(self._agent_dir):
                parser.error(
                    f'An agent named "{self._agent}" already exists, run "stop" first.'
                )
            image = params["image"]
            if image is not None and image not in self._get_images():
                parser.error(
                    f'Invalid "--image" for {params["provider"]}, '
                    f'possible values: {", ".join(self._get_images())}'
                )
        elif parser_action in ("stop", "ssh", "show"):
            if not _os.path.isdir(self._agent_dir):
                parser.error(f'No agent named "{self._agent}", run "start" first.')
        elif parser_action not in ("list", "images", "version"):
            parser.error("An action is required")

        try:
            getattr(self, f"_{parser_action}")()
        except KeyboardInterrupt:  # pragma: no cover
            parser.exit(status=1, message="Interrupted by user\n")
        except Exception as exception:
            if self._debug:
                raise
            parser.error(str(exception))

    def _start(self):
        """Start the agent."""
        from json import dump
        from secrets import token_hex

        print("Initializing agent parameters...")
        provider = self._params["provider"]
        for key in ("ansiblePlaybook", "ansibleRequirements"):
            try:
                self._params[key] = _os.path.realpath(
                    _os.path.expanduser(self._params[key])
                )
            except TypeError:
                continue
            if not _os.path.isfile(self._params[key]):
                raise FileNotFoundError(self._params[key])

        self._params["agentName"] = agent_name = f"acid{token_hex(12).lower()}"
        for key, parameter in (
            ("AZURE_AGENT_SHUTDOWN_TIMEOUT", "timeout"),
            ("AZURE_AGENT_NAME", "agentName"),
            ("AZURE_AGENT_POOL", "agentPool"),
            ("AZURE_AGENT_URL", "agentOrganizationUrl"),
            ("AZURE_AGENT_TOKEN", "agentManagerToken"),
            ("AZURE_AGENT_VERSION", "agentVersion"),
            ("AZURE_AGENT_IN_MEMORY_WORK_DIR", "inMemoryWorkDir"),
            ("AZURE_AGENT_ENV", "agentEnv"),
        ):
            if self._params[parameter] is not None:
                _os.environ[key] = self._params[parameter]
        del self._params["agentManagerToken"]

        tf_vars = {
            key: self._params[key]
            for key in (
                "image",
                "instanceType",
                "spot",
                "resourceGroupName",
                "virtualNetworkName",
                "volumeSize",
            )
            if self._params[key]
        }
        tf_vars["name"] = agent_name

        _os.makedirs(self._agent_dir, exist_ok=True)
        _os.chmod(self._agent_dir, 0o700)
        with open(_os.path.join(self._agent_dir, "parameters.json"), "wt") as file:
            dump(self._params, file)
        with open(
            _os.path.join(self._agent_dir, "terraform.tfvars.json"), "wt"
        ) as json_file:
            dump(tf_vars, json_file)
        agent_src = _os.path.join(_AGENTS_SRC, provider)
        for name in _os.listdir(agent_src):
            _os.symlink(
                _os.path.join(agent_src, name), _os.path.join(self._agent_dir, name)
            )
        print(f"Agent resource name: {agent_name}")
        print("Initializing Ansible...")
        if self._params["ansibleRequirements"]:
            _os.makedirs(_ANSIBLE_ROLES, exist_ok=True)
            galaxy_cmd = [
                "ansible-galaxy",
                "install",
                "-p",
                _ANSIBLE_ROLES,
                "-r",
                self._params["ansibleRequirements"],
            ]
            if self._force_update:
                galaxy_cmd.append("--force-with-deps")
            self._call(galaxy_cmd, capture_output=True)

        self.tf_run_with_retries(
            ["apply", "-auto-approve", "-input=false"], "Starting agent..."
        )

        from ansible_run import ansible_run

        _os.environ["ANSIBLE_ROLES_PATH"] = f"{_ANSIBLE_ROLES}:{_ACID_DIR}/roles"
        ansible_run(
            ansible_playbook=self._params["ansiblePlaybook"], terraform=self._terraform
        )

        print("Operation completed")

    def tf_run_with_retries(self, args, msg):
        """
        Init and run terraform with retries.

        Args:
            args (list of str): Terraform arguments.
            msg (str): Message.
        """
        _sys.path.append(_AGENTS_SRC)
        from tf_run import tf_run

        print("Initializing Terraform...")
        tf_env = _os.environ.copy()
        tf_env["TF_PLUGIN_CACHE_DIR"] = _TF_PLUGINS
        init_cmd = [self._terraform, "init", "-input=false"]
        if self._force_update:
            init_cmd.append("-upgrade=true")
        self._call(init_cmd, env=tf_env, capture_output=True)

        print(msg)
        _os.chdir(self._agent_dir)
        tf_run(self._terraform, args)

    def _stop(self):
        """Stop the agent."""
        if not self._params["force"]:
            confirm = ""
            while confirm != "y":
                confirm = (
                    input(
                        f"Confirm the destruction of the agent "
                        f'"{self._params["agentDescription"]}" (y/n): '
                    )
                    .strip()
                    .lower()
                )
                if confirm == "n":
                    print("Operation cancelled")
                    return

        self._params.update(self._get_parameters())
        self.tf_run_with_retries(
            ["destroy", "-auto-approve", "-input=false"], "Stopping agent..."
        )
        from shutil import rmtree

        rmtree(self._agent_dir, ignore_errors=True)
        print("Operation completed")

    @staticmethod
    def _list():
        """
        List agents.
        """
        print("\n".join(_os.listdir(AGENTS_DIR)))

    def _show(self):
        """Show the agent parameters and outputs."""
        print(
            "PARAMETERS:",
            "\n".join(f"- {k}={v}" for k, v in self._get_parameters().items()),
            "OUTPUTS:",
            f"- agentDirectory={self._agent_dir}",
            "\n".join(f"- {k}={v}" for k, v in self._tf_output(False).items()),
            sep="\n",
        )

    def _images(self):
        """List images for a provider"""
        print("\n".join(self._get_images()))

    def _ssh(self):
        """SSH to the agent."""
        ssh_args = self._params["ssh_args"]
        if "-i" in ssh_args:
            raise ValueError('Remove "-i" SSH argument, it is managed by Acid.')
        out = self._tf_output()

        cwd = _os.getcwd()
        _os.chdir(self._agent_dir)

        private_key = _os.path.realpath(out["privateKey"])
        user = out["user"]
        try:
            ip_address = out["ipAddress"]
        except KeyError:
            raise RuntimeError(
                "Unable to get the instance IP address. This can be caused by "
                'an unsuccessful "acid start". You can connect using the following SSH '
                "command with the proper IP address: "
                f'"ssh -i {private_key} {user}@IP_ADDRESS"'
            )

        from subprocess import run

        run(
            [
                "ssh",
                f"{user}@{ip_address}",
                "-i",
                private_key,
                "-o",
                "StrictHostKeyChecking=no",
            ]
            + [arg for arg in ssh_args if arg != "--"],
            cwd=cwd,
        )

    @staticmethod
    def _version():
        """Show version"""
        with open(_os.path.join(_ACID_DIR, "version")) as file:
            print(file.read().strip())

    def _call(self, command, capture_output=False, check=True, **kwargs):
        """
        Call a command with automatic error handling.

        Args:
            command (iterable of str or str):
            capture_output (bool): If True, capture stdout.
            check (bool): If True, check return code.
            kwargs: subprocess.run keyword arguments.

        Returns:
            subprocess.CompletedProcess
        """
        from subprocess import run, PIPE

        command_kwargs = dict(
            universal_newlines=True,
            stderr=PIPE,
            stdout=(PIPE if capture_output else None),
            cwd=self._agent_dir,
        )
        command_kwargs.update(kwargs)
        process = run(command, **command_kwargs)
        if process.returncode and check:
            stderr = process.stderr.strip()
            stderr = f"\nStderr messages:\n{stderr}" if stderr else ""
            raise RuntimeError(f"Error code: {process.returncode}{stderr}")
        return process

    @property
    def _terraform(self):
        """
        Get utility executable path after installing it.

        Returns:
            str: Terraform executable path.
        """
        if self._terraform_path:
            return self._terraform_path

        self._terraform_path = _os.path.join(_TF, "terraform")
        if _os.path.isfile(self._terraform_path) and not self._force_update:
            return self._terraform_path

        import requests
        import platform
        import zipfile
        import io

        response = requests.get(
            "https://checkpoint-api.hashicorp.com/v1/check/terraform"
        )
        response.raise_for_status()
        last_release = response.json()
        download_url = last_release["current_download_url"].rstrip("/")
        arch = platform.machine().lower()
        arch = {"x86_64": "amd64"}.get(arch, arch)
        archive_url = (
            f"{download_url}/terraform_{last_release['current_version']}_"
            f"{platform.system().lower()}_{arch}.zip"
        )
        response = requests.get(archive_url)
        response.raise_for_status()
        compressed = io.BytesIO(response.content)
        compressed.seek(0)
        with zipfile.ZipFile(compressed) as compressed_file:
            _os.makedirs(_TF_PLUGINS, exist_ok=True)
            self._terraform_path = compressed_file.extract(
                compressed_file.namelist()[0], path=_TF
            )
        _os.chmod(self._terraform_path, _os.stat(self._terraform_path).st_mode | 0o111)
        return self._terraform_path

    def _tf_output(self, check=True):
        """
        Get the agent Terraform output.

        Args:
            check (bool): If True, check if command failed.
        """
        from json import loads

        output = self._call(
            (self._terraform, "output", "-json"),
            capture_output=True,
            check=check,
        )
        if not check and output.returncode:
            return dict()
        return {key: value["value"] for key, value in loads(output.stdout).items()}

    def _get_parameters(self):
        """Get the agent parameters."""
        from json import load

        with open(_os.path.join(self._agent_dir, "parameters.json"), "rb") as file:
            return load(file)

    def _get_images(self, provider=None):
        """
        Get available images for a provider.

        Args:
            provider (str): Provider, if not specified, get it from parameters.

        Returns:
            list of str: Images names.
        """
        from json import load

        if provider is None:
            provider = self._params["provider"]
        with open(
            _os.path.join(_AGENTS_SRC, provider, "images.auto.tfvars.json"), "rb"
        ) as file:
            return sorted(load(file)["images"].keys())

    def _images_completer(self, prefix, parsed_args, **_):
        """
        Autocomplete images.

        Args:
            prefix (str): Provider prefix to filter.
            parsed_args (argparse.Namespace): CLI arguments.

        Returns:
            iterable of str: Images names.
        """
        provider = parsed_args.provider
        if provider:
            return (
                image
                for image in self._get_images(provider)
                if image.startswith(prefix)
            )


def _command():
    """run"""
    _Command()


if __name__ == "__main__":  # pragma: no branch
    _command()
