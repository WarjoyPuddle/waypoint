# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import json
import multiprocessing
import pathlib

from .file_types import is_cmake_file
from .file_types import is_cpp_file
from .file_types import is_json_file
from .file_types import is_python_file
from .process import run
from .system import get_cpu_count
from .system import get_python


def check_formatting_cmake(file: pathlib.Path) -> tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "--check",
            str(file),
        ]
    )
    if not success:
        return False, output

    return True, None


def check_formatting_cpp(
    file: pathlib.Path, path_to_config: pathlib.Path
) -> tuple[bool, str | None]:
    success, output = run(
        [
            "clang-format-20",
            f"--style=file:{path_to_config}",
            "--dry-run",
            "-Werror",
            str(file),
        ]
    )
    if not success:
        return False, output

    return True, None


def check_formatting_json(file: pathlib.Path) -> tuple[bool, str | None]:
    with open(file, "r") as f:
        original = f.read()
    with open(file, "r") as f:
        data = json.load(f)

    data_str = json.dumps(data, indent=2, sort_keys=True)
    data_str += "\n"

    success = data_str == original
    if not success:
        return False, f"Incorrect JSON file formatting ({file})\n"

    return True, None


def check_formatting_python(file: pathlib.Path) -> tuple[bool, str | None]:
    success, output = run(
        [
            get_python(),
            "-m",
            "isort",
            "--check",
            "--combine-star",
            "--float-to-top",
            "--force-single-line-imports",
            "--ignore-whitespace",
            "--sort-reexports",
            "--star-first",
            "--line-length",
            "88",
            str(file),
        ]
    )
    if not success:
        return False, output

    success, output = run(
        ["black", "--quiet", "--check", "--line-length", "88", str(file)]
    )
    if not success:
        return False, output

    return True, None


def format_cmake(file: pathlib.Path) -> tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "-i",
            str(file),
        ]
    )
    if not success:
        return False, output

    return True, None


def format_cpp(
    f: pathlib.Path, path_to_config: pathlib.Path
) -> tuple[bool, str | None]:
    success, output = run(
        [
            "clang-format-20",
            f"--style=file:{path_to_config}",
            "-i",
            str(f),
        ]
    )
    if not success:
        return False, output

    return True, None


def format_json(file: pathlib.Path) -> tuple[bool, str | None]:
    with open(file, "r") as f:
        original = f.read()
    with open(file, "r") as f:
        data = json.load(f)

    data_str = json.dumps(data, indent=2, sort_keys=True)
    data_str += "\n"
    if data_str != original:
        with open(file, "w") as f:
            f.write(data_str)

    return True, None


def format_python(file: pathlib.Path) -> tuple[bool, str | None]:
    success, output = run(
        [
            get_python(),
            "-m",
            "isort",
            "--combine-star",
            "--float-to-top",
            "--force-single-line-imports",
            "--ignore-whitespace",
            "--sort-reexports",
            "--star-first",
            "--line-length",
            "88",
            str(file),
        ]
    )
    if not success:
        return False, output

    success, output = run(["black", "--quiet", "--line-length", "88", str(file)])
    if not success:
        return False, output

    return True, None


def fix_lines(lines: list[str]) -> str:
    lines = [line.rstrip() for line in lines]
    while lines[0] == "":
        lines.pop(0)
    while lines[-1] == "":
        lines.pop(-1)

    lines = [line.replace("\t", "  ") for line in lines]

    return "\n".join(lines) + "\n"


def fix_whitespace(file: pathlib.Path) -> bool:
    with open(file, "r") as f:
        lines = f.readlines()

    text = fix_lines(lines)

    with open(file, "w") as f:
        f.write(text)

    return True


def check_whitespace(file: pathlib.Path) -> bool:
    with open(file, "r") as f:
        lines = f.readlines()

    original = "".join(lines)
    text = fix_lines(lines)

    return text == original


def check_formatting_in_single_file(data) -> tuple[bool, str | None, pathlib.Path]:
    file, path_to_clang_format_config = data

    success = True
    output = None

    if is_cmake_file(file):
        success, output = check_formatting_cmake(file)
    if is_cpp_file(file):
        success, output = check_formatting_cpp(file, path_to_clang_format_config)
    if is_json_file(file):
        success, output = check_formatting_json(file)
    if is_python_file(file):
        success, output = check_formatting_python(file)

    success = success and check_whitespace(file)

    return success, output, file


def format_single_file(data) -> tuple[bool, str | None, pathlib.Path]:
    file, path_to_clang_format_config = data

    success = True
    output = None

    if is_cmake_file(file):
        success, output = format_cmake(file)
    if is_cpp_file(file):
        success, output = format_cpp(file, path_to_clang_format_config)
    if is_json_file(file):
        success, output = format_json(file)
    if is_python_file(file):
        success, output = format_python(file)

    success = success and fix_whitespace(file)

    return success, output, file


def format_files(files, clang_format_config) -> bool:
    inputs = [
        (file, clang_format_config if is_cpp_file(file) else None) for file in files
    ]

    with multiprocessing.Pool(get_cpu_count()) as pool:
        results = pool.map(format_single_file, inputs)
        errors = [(output, file) for success, output, file in results if not success]
        if len(errors) > 0:
            for output, file in errors:
                if output is not None:
                    print(output)
                print(f"Error formatting file {file}")

            return False

    return True


def check_formatting(
    files: list[pathlib.Path], clang_format_config: pathlib.Path
) -> bool:
    inputs = [
        (file, clang_format_config if is_cpp_file(file) else None) for file in files
    ]

    with multiprocessing.Pool(get_cpu_count()) as pool:
        results = pool.map(check_formatting_in_single_file, inputs)
        errors = [(output, file) for success, output, file in results if not success]
        if len(errors) > 0:
            for output, file in errors:
                if output is not None:
                    print(output)
                print(
                    f"Error: {file}\nIncorrect formatting; run scripts/format_code.sh"
                )

            return False

    return True
