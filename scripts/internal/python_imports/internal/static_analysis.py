# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import json
import multiprocessing
import os
import time
import typing

from .cmake import build_dir_from_preset
from .process import run
from .system import get_cpu_count


def get_files_from_compilation_database(preset, cmake_source_dir) -> typing.List[str]:
    build_dir = build_dir_from_preset(preset, cmake_source_dir)
    compilation_db = os.path.realpath(f"{build_dir}/compile_commands.json")
    assert os.path.isfile(compilation_db)

    with open(compilation_db, "r") as f:
        data = json.load(f)

    files = set()
    for d in data:
        files.add(d["file"])

    files = [os.path.realpath(f) for f in files]
    files = [f for f in files if "___" not in f]
    files.sort()
    for f in files:
        assert os.path.isfile(f), f"File not found: {f}"

    return files


def clang_tidy_process_single_file(data) -> typing.Tuple[bool, str, float, str | None]:
    file, preset, cmake_source_dir, project_root_dir, config_path = data

    build_dir = build_dir_from_preset(preset, cmake_source_dir)

    with contextlib.chdir(project_root_dir):
        start_time = time.time_ns()
        success, output = run(
            [
                "clang-tidy-20",
                f"--config-file={config_path}",
                "-p",
                build_dir,
                file,
            ]
        )
        duration = time.time_ns() - start_time

    return (
        success,
        file,
        duration,
        None if success else (None if output is None else output.strip()),
    )


def run_clang_static_analysis(inputs) -> bool:
    if len(inputs) == 0:
        return True

    inputs = list(set(inputs))
    inputs.sort()

    success = run_clang_tidy(inputs)
    if not success:
        return False

    return True


def run_clang_tidy(inputs) -> bool:
    with multiprocessing.Pool(get_cpu_count()) as pool:
        results = pool.map(clang_tidy_process_single_file, inputs)

        errors = [
            (file, stdout) for success, file, duration, stdout in results if not success
        ]
        if len(errors) > 0:
            for f, stdout in errors:
                print(f"Error running clang-tidy on {f}")
                if stdout is not None:
                    print(stdout)

            return False

    return True
