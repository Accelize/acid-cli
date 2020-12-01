#! /usr/bin/env python3
"""Setup script"""
from os import chdir
from os.path import dirname, abspath, join
from setuptools import setup, find_packages
from subprocess import run


PACKAGE_INFO = dict(
    name="acidcli",
    description="On-demand Azure Pipeline cloud self-hosted agent",
    long_description_content_type="text/markdown; charset=UTF-8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: System :: Installation/Setup",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: POSIX :: Linux",
    ],
    keywords="azure pipeline agent",
    author="Accelize",
    url="https://github.com/Accelize/acid",
    project_urls={"Download": "https://pypi.org/project/acid"},
    license="Apache License, Version 2.0",
    python_requires=">=3.6",
    install_requires=["python-dateutil", "requests", "ansible>=2.8", "argcomplete"],
    setup_requires=["setuptools"],
    tests_require=["pytest"],
    packages=find_packages(exclude=["agents", "tests"]),
    include_package_data=True,
    zip_safe=False,
    command_options={},
    entry_points={"console_scripts": ["acid=acidcli.__init__:_command"]},
)

SETUP_DIR = abspath(dirname(__file__))
run(("git", "-C", SETUP_DIR, "submodule", "update", "--remote", "--init"))
for key, filename in (("version", "version"), ("long_description", "readme.md")):
    with open(join(SETUP_DIR, f"acidcli/acid/{filename}")) as file:
        PACKAGE_INFO[key] = file.read().strip().lstrip("v")

if __name__ == "__main__":
    chdir(SETUP_DIR)
    setup(**PACKAGE_INFO)
