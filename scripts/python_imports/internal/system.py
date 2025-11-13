# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import os
import pathlib
import platform
import shutil
import sys


def get_cpu_count() -> int:
    if "process_cpu_count" in dir(os):
        return os.process_cpu_count()

    return os.cpu_count()


class NewEnv:
    def __init__(self, env):
        self.backup = os.environ.copy()
        self.env = env

    def __enter__(self):
        os.environ.clear()
        os.environ.update(self.env)

        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.environ.clear()
        os.environ.update(self.backup)

        return False


def is_linux():
    return platform.system() == "Linux"


def is_supported_os() -> bool:
    if is_linux():
        return True
    print(f"Unsupported OS: {platform.system()}")

    return False


def recursively_copy_dir(source, destination):
    shutil.copytree(source, destination, dirs_exist_ok=True)


def remove_dir(path):
    if os.path.exists(path) and os.path.isdir(path):
        shutil.rmtree(path)


def create_dir(path) -> bool:
    if os.path.exists(path) and not os.path.isdir(path):
        return False

    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

    return True


def get_python() -> str:
    return (
        "python3"
        if (sys.executable is None or sys.executable == "")
        else sys.executable
    )
