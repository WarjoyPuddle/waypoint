# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import pathlib

from python_imports import ensure_hooks_installed

THIS_SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
PROJECT_ROOT_DIR = THIS_SCRIPT_DIR.parent.parent.resolve()


def main() -> int:
    success = ensure_hooks_installed(PROJECT_ROOT_DIR)
    if not success:
        return 1

    return 0


if __name__ == "__main__":
    assert pathlib.Path.cwd() == PROJECT_ROOT_DIR
    exit(main())
