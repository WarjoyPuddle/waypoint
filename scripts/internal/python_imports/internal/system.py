# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import os
import pathlib
import platform
import shutil
import sys


def get_cpu_count() -> int:
    if "process_cpu_count" in dir(os):
        return os.process_cpu_count()

    return os.cpu_count()


@contextlib.contextmanager
def new_env(env_):
    backup = os.environ.copy()
    env = env_.copy()

    try:
        os.environ.clear()
        os.environ.update(env)

        yield None

        os.environ.clear()
        os.environ.update(backup)
    finally:
        pass


def is_linux():
    return platform.system() == "Linux"


def is_supported_os() -> bool:
    if is_linux():
        return True
    print(f"Unsupported OS: {platform.system()}")

    return False


def recursively_copy_dir(source: pathlib.Path, destination: pathlib.Path):
    shutil.copytree(source, destination, dirs_exist_ok=True)


def remove_dir(path: pathlib.Path):
    if path.exists() and path.is_dir():
        shutil.rmtree(path)


def create_dir(path: pathlib.Path) -> bool:
    if path.exists() and not path.is_dir():
        return False

    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    return True


def get_python() -> str:
    return (
        "python3"
        if (sys.executable is None or sys.executable == "")
        else sys.executable
    )
