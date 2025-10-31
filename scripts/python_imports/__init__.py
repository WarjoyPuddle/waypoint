# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

from .internal.checks import (
    misc_checks,
    verify_installation_contents_shared,
    verify_installation_contents_static,
)
from .internal.cmake import (
    build_cmake,
    build_dir_from_preset,
    clean_build_dir,
    clean_install_dir,
    configure_cmake,
    install_cmake,
    install_dir_from_preset,
    run_ctest,
)
from .internal.coverage import analyze_gcc_coverage, process_coverage
from .internal.files import (
    changed_cpp_source_files_and_dependents,
    find_all_cpp_source_files,
)
from .internal.formatting import check_formatting, format_files
from .internal.legal import check_copyright_comments, check_license_file
from .internal.process import run
from .internal.static_analysis import (
    get_files_from_compilation_database,
    run_clang_static_analysis,
)
from .internal.system import NewEnv, is_supported_os, recursively_copy_dir, remove_dir
from .internal.Task import Task
