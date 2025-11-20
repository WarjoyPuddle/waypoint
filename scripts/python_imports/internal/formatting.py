# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import json
import multiprocessing
import typing

from .file_types import is_cmake_file
from .file_types import is_cpp_file
from .file_types import is_json_file
from .file_types import is_python_file
from .process import run
from .system import get_cpu_count
from .system import get_python


def check_formatting_cmake(file) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "--check",
            file,
        ]
    )
    if not success:
        return False, output

    return True, None


def check_formatting_cpp(file, path_to_config) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "clang-format-20",
            f"--style=file:{path_to_config}",
            "--dry-run",
            "-Werror",
            file,
        ]
    )
    if not success:
        return False, output

    return True, None


def check_formatting_json(file) -> typing.Tuple[bool, str | None]:
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


def check_formatting_python(file) -> typing.Tuple[bool, str | None]:
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
            file,
        ]
    )
    if not success:
        return False, output

    success, output = run(["black", "--quiet", "--check", "--line-length", "88", file])
    if not success:
        return False, output

    return True, None


def format_cmake(file) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "-i",
            file,
        ]
    )
    if not success:
        return False, output

    return True, None


def format_cpp(f, path_to_config) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "clang-format-20",
            f"--style=file:{path_to_config}",
            "-i",
            f,
        ]
    )
    if not success:
        return False, output

    return True, None


def format_json(file) -> typing.Tuple[bool, str | None]:
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


def format_python(file) -> typing.Tuple[bool, str | None]:
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
            file,
        ]
    )
    if not success:
        return False, output

    success, output = run(["black", "--quiet", "--line-length", "88", file])
    if not success:
        return False, output

    return True, None


def check_formatting_in_single_file(data) -> typing.Tuple[bool, str | None, str]:
    file, path_to_clang_format_config = data

    if is_cmake_file(file):
        success, output = check_formatting_cmake(file)

        return success, output, file
    if is_cpp_file(file):
        success, output = check_formatting_cpp(file, path_to_clang_format_config)

        return success, output, file
    if is_json_file(file):
        success, output = check_formatting_json(file)

        return success, output, file
    if is_python_file(file):
        success, output = check_formatting_python(file)

        return success, output, file

    return (
        False,
        f"Expected to check formatting in unsupported file type ({file})\n",
        file,
    )


def format_single_file(data) -> typing.Tuple[bool, str | None, str]:
    file, path_to_clang_format_config = data

    if is_cmake_file(file):
        success, output = format_cmake(file)

        return success, output, file
    if is_cpp_file(file):
        success, output = format_cpp(file, path_to_clang_format_config)

        return success, output, file
    if is_json_file(file):
        success, output = format_json(file)

        return success, output, file
    if is_python_file(file):
        success, output = format_python(file)

        return success, output, file

    return False, "Expected to format unsupported file type\n", file


def is_file_in_need_of_formatting(file) -> bool:
    return (
        is_cmake_file(file)
        or is_cpp_file(file)
        or is_json_file(file)
        or is_python_file(file)
    )


def format_files(files, clang_format_config) -> bool:
    inputs = [f for f in files if is_file_in_need_of_formatting(f)]
    inputs = [
        (file, clang_format_config if is_cpp_file(file) else None) for file in inputs
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


def check_formatting(files, clang_format_config) -> bool:
    inputs = [f for f in files if is_file_in_need_of_formatting(f)]
    inputs = [
        (file, clang_format_config if is_cpp_file(file) else None) for file in inputs
    ]

    with multiprocessing.Pool(get_cpu_count()) as pool:
        results = pool.map(check_formatting_in_single_file, inputs)
        errors = [(output, file) for success, output, file in results if not success]
        if len(errors) > 0:
            for output, file in errors:
                if output is not None:
                    print(output)
                print(
                    f'Error: {file}\nIncorrect formatting; run the build in "format" mode'
                )

            return False

    return True
