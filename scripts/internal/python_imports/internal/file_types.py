# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import pathlib


def is_shell_script(f: pathlib.Path) -> bool:
    return f.suffix == ".bash" or f.suffix == ".sh"


def is_cmake_file(f: pathlib.Path) -> bool:
    return f.name == "CMakeLists.txt" or f.suffix == ".cmake"


def is_cpp_header_file(f: pathlib.Path) -> bool:
    return f.suffix == ".hpp"


def is_cpp_source_file(f: pathlib.Path) -> bool:
    return f.suffix == ".cpp"


def is_cpp_file(f: pathlib.Path) -> bool:
    return is_cpp_source_file(f) or is_cpp_header_file(f)


def is_docker_file(f: pathlib.Path) -> bool:
    return f.name == "Dockerfile" or f.suffix == ".dockerfile"


def is_json_file(f: pathlib.Path) -> bool:
    return f.suffix == ".json"


def is_python_file(f: pathlib.Path) -> bool:
    return f.suffix == ".py"
