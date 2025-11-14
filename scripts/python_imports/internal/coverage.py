# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import json

from .cmake import build_dir_from_preset
from .process import run
from .system import create_dir


def run_gcovr(
    build_dir,
    project_root_dir,
    coverage_dir_gcovr,
    coverage_file_html_gcovr,
    coverage_file_json_gcovr,
) -> bool:
    success = create_dir(coverage_dir_gcovr)
    if not success:
        print(f"Failed to create {coverage_dir_gcovr}")

        return False

    with contextlib.chdir(project_root_dir):
        success, output = run(
            [
                "gcovr",
                "--decisions",
                "--exclude-pattern-prefix",
                "GCOV_COVERAGE_58QuSuUgMN8onvKx_*",
                "--exclude",
                f"{project_root_dir}/test/",
                "--filter",
                project_root_dir,
                "--gcov-object-directory",
                build_dir,
                "--html-details",
                coverage_file_html_gcovr,
                "--html-theme",
                "github.dark-green",
                "--json-summary",
                coverage_file_json_gcovr,
                "--json-summary-pretty",
                "--root",
                project_root_dir,
                "--sort",
                "uncovered-percent",
                "--verbose",
            ]
        )
        if not success:
            print("Error running gcovr")
            if output is not None:
                print(output)

            return False

    return True


def process_coverage(
    preset,
    cmake_source_dir,
    project_root_dir,
    coverage_dir_gcovr,
    coverage_file_html_gcovr,
    coverage_file_json_gcovr,
) -> bool:
    build_dir = build_dir_from_preset(preset, cmake_source_dir)

    success = run_gcovr(
        build_dir,
        project_root_dir,
        coverage_dir_gcovr,
        coverage_file_html_gcovr,
        coverage_file_json_gcovr,
    )
    if not success:
        return False

    return True


def analyze_gcc_coverage(coverage_file_json_gcovr) -> bool:
    with open(coverage_file_json_gcovr, "r") as f:
        data = json.load(f)

    all_branches_covered = data["branch_covered"] == data["branch_total"]
    all_decisions_covered = data["decision_covered"] == data["decision_total"]
    all_functions_covered = data["function_covered"] == data["function_total"]
    all_lines_covered = data["line_covered"] == data["line_total"]

    if (
        not all_branches_covered
        or not all_decisions_covered
        or not all_functions_covered
        or not all_lines_covered
    ):
        print("Incomplete coverage")
        return False

    return True
