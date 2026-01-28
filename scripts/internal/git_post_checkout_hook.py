# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import os

from python_imports import ensure_hooks_installed

THIS_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.path.realpath(f"{THIS_SCRIPT_DIR}/../..")


def main() -> int:
    success = ensure_hooks_installed(PROJECT_ROOT_DIR)
    if not success:
        return 1

    return 0


if __name__ == "__main__":
    assert os.getcwd() == PROJECT_ROOT_DIR
    exit(main())
