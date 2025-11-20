# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import os
import re


def is_bash_file(f) -> bool:
    return re.search(r"\.bash$", f) is not None


def is_cmake_file(f) -> bool:
    return (
        re.search(r"CMakeLists\.txt$", f) is not None
        or re.search(r"\.cmake$", f) is not None
    )


def is_cpp_header_file(f) -> bool:
    return re.search(r"\.hpp$", f) is not None


def is_cpp_source_file(f) -> bool:
    return re.search(r"\.cpp$", f) is not None


def is_cpp_file(f) -> bool:
    return is_cpp_source_file(f) or is_cpp_header_file(f)


def is_docker_file(f) -> bool:
    return (
        re.search(r"\.dockerfile$", f) is not None
        or re.search(r"^Dockerfile$", os.path.basename(f)) is not None
    )


def is_json_file(f) -> bool:
    return re.search(r"\.json$", f) is not None


def is_python_file(f) -> bool:
    return re.search(r"\.py$", f) is not None
