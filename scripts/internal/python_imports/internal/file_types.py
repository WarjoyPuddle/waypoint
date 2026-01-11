# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import pathlib
import re


def is_shell_script(f: pathlib.Path) -> bool:
    return (
        re.search(r"\.bash$", str(f)) is not None
        or re.search(r"\.sh$", str(f)) is not None
    )


def is_cmake_file(f: pathlib.Path) -> bool:
    return (
        re.search(r"CMakeLists\.txt$", str(f)) is not None
        or re.search(r"\.cmake$", str(f)) is not None
    )


def is_cpp_header_file(f: pathlib.Path) -> bool:
    return re.search(r"\.hpp$", str(f)) is not None


def is_cpp_source_file(f: pathlib.Path) -> bool:
    return re.search(r"\.cpp$", str(f)) is not None


def is_cpp_file(f: pathlib.Path) -> bool:
    return is_cpp_source_file(f) or is_cpp_header_file(f)


def is_docker_file(f: pathlib.Path) -> bool:
    return (
        re.search(r"\.dockerfile$", str(f)) is not None
        or re.search(r"^Dockerfile$", f.name) is not None
    )


def is_json_file(f: pathlib.Path) -> bool:
    return re.search(r"\.json$", str(f)) is not None


def is_python_file(f: pathlib.Path) -> bool:
    return re.search(r"\.py$", str(f)) is not None
