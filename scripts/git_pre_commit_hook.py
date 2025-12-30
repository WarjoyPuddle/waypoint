# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import os

from python_imports import check_copyright_comments
from python_imports import check_formatting
from python_imports import check_license_file
from python_imports import get_files_staged_for_commit

THIS_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_ROOT_DIR = os.path.realpath(f"{THIS_SCRIPT_DIR}/..")
INFRASTRUCTURE_DIR = os.path.realpath(f"{PROJECT_ROOT_DIR}/infrastructure")

CLANG_FORMAT_CONFIG = os.path.realpath(f"{INFRASTRUCTURE_DIR}/.clang-format-20")

LICENSE_FILE_PATH = f"{PROJECT_ROOT_DIR}/LICENSE"


def main() -> int:
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
    assert os.getcwd() == PROJECT_ROOT_DIR
    exit(main())
