# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import pathlib

from python_imports import check_copyright_comments
from python_imports import check_formatting
from python_imports import check_license_file
from python_imports import ensure_hooks_installed
from python_imports import get_files_staged_for_commit

THIS_SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
PROJECT_ROOT_DIR = THIS_SCRIPT_DIR.parent.parent.resolve()
INFRASTRUCTURE_DIR = PROJECT_ROOT_DIR / "infrastructure"

CLANG_FORMAT_CONFIG = INFRASTRUCTURE_DIR / ".clang-format-20"

LICENSE_FILE_PATH = PROJECT_ROOT_DIR / "LICENSE"


def main() -> int:
    success = ensure_hooks_installed(PROJECT_ROOT_DIR)
    if not success:
        return 1

    success = check_license_file(LICENSE_FILE_PATH)
    if not success:
        return 1

    files = get_files_staged_for_commit(PROJECT_ROOT_DIR)

    success = check_copyright_comments(files)
    if not success:
        return 1

    success = check_formatting(files, CLANG_FORMAT_CONFIG)
    if not success:
        return 1

    return 0


if __name__ == "__main__":
    assert pathlib.Path.cwd() == PROJECT_ROOT_DIR
    exit(main())
