# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import json
import multiprocessing
import typing

from .files import (
    find_files_by_name,
    is_cmake_file,
    is_cpp_file,
    is_json_file,
    is_python_file,
)
from .process import run
from .system import get_cpu_count, get_python


def check_formatting_cmake(f) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "--check",
            f,
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


def check_formatting_json(f) -> typing.Tuple[bool, str | None]:
    with open(f, "r") as handle:
        original = handle.read()
    with open(f, "r") as handle:
        data = json.load(handle)

    data_str = json.dumps(data, indent=2, sort_keys=True)
    data_str += "\n"

    success = data_str == original
    if not success:
        return False, "Incorrect JSON file formatting\n"

    return True, None


def check_formatting_python(file) -> typing.Tuple[bool, str | None]:
    success, output = run(["black", "--quiet", "--check", "--line-length", "88", file])
    if not success:
        return False, output

    return True, None


def format_cmake(f) -> typing.Tuple[bool, str | None]:
    success, output = run(
        [
            "cmake-format",
            "--enable-markup",
            "FALSE",
            "-i",
            f,
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


def format_json(f) -> typing.Tuple[bool, str | None]:
    with open(f, "r") as handle:
        original = handle.read()
    with open(f, "r") as handle:
        data = json.load(handle)

    data_str = json.dumps(data, indent=2, sort_keys=True)
    data_str += "\n"
    if data_str != original:
        with open(f, "w") as handle:
            handle.write(data_str)

    return True, None


def format_python(f) -> typing.Tuple[bool, str | None]:
    success, output = run([get_python(), "-m", "isort", "--line-length", "88", f])
    assert success

    success, output = run(["black", "--quiet", "--line-length", "88", f])
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

    return False, "Expected to check formatting in unsupported file type\n", file


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


def is_file_for_formatting(f) -> bool:
    return is_cmake_file(f) or is_cpp_file(f) or is_json_file(f) or is_python_file(f)


def format_files(root_dir, clang_format_config) -> bool:
    files = find_files_by_name(root_dir, is_file_for_formatting)
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


def check_formatting(root_dir, clang_format_config) -> bool:
    files = find_files_by_name(root_dir, is_file_for_formatting)
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
                    f'Error: {file}\nIncorrect formatting; run the build in "format" mode'
                )

            return False

    return True
