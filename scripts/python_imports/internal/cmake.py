# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import json
import os
import pathlib
import typing

from .compiler import Compiler
from .process import run
from .system import NewEnv
from .system import get_cpu_count
from .system import recursively_copy_dir
from .system import remove_dir

CLANG20_ENV_PATCH = {"CC": "clang-20", "CXX": "clang++-20"}
GCC15_ENV_PATCH = {"CC": "gcc-15", "CXX": "g++-15"}

EXPORT_COMPILE_COMMANDS_ENV_PATCH = {"CMAKE_EXPORT_COMPILE_COMMANDS": "TRUE"}


def env_patch_from_preset(preset):
    if preset.compiler == Compiler.Clang:
        return CLANG20_ENV_PATCH
    if preset.compiler == Compiler.Gcc:
        return GCC15_ENV_PATCH

    assert False, "Unreachable"


def configure_cmake(preset, cmake_source_dir) -> bool:
    env_patch = env_patch_from_preset(preset)

    env = os.environ.copy()
    env.update(env_patch)
    env.update(EXPORT_COMPILE_COMMANDS_ENV_PATCH)
    with NewEnv(env):
        build_dir = build_dir_from_preset(preset, cmake_source_dir)

        if os.path.exists(build_dir):
            return True

        pathlib.Path(build_dir).mkdir(parents=True, exist_ok=True)

        with contextlib.chdir(cmake_source_dir):
            command = ["cmake", "--preset", f"{preset.configure}"]
            success, output = run(command)
            if not success:
                if output is not None:
                    print(output)

                return False

    return True


def build_cmake(config, preset, cmake_source_dir, target) -> bool:
    with contextlib.chdir(cmake_source_dir):
        success, output = run(
            [
                "cmake",
                "--build",
                "--preset",
                f"{preset.build}",
                "--config",
                f"{config}",
                "--target",
                f"{target}",
                "--parallel",
                f"{get_cpu_count()}",
            ]
        )
        if not success:
            if output is not None:
                print(output)

            return False

    return True


def run_ctest(preset, build_config, label_include_regex, cmake_source_dir) -> bool:
    with contextlib.chdir(cmake_source_dir):
        cmd = [
            "ctest",
            "--preset",
            preset.test,
            "--build-config",
            f"{build_config}",
            "--parallel",
            f"{get_cpu_count()}",
        ]
        if label_include_regex is not None:
            cmd += [
                "--label-regex",
                label_include_regex,
            ]

        success, output = run(cmd)
        if not success:
            if output is not None:
                print(output)

            return False

    return True


def install_cmake(preset, config, working_dir) -> bool:
    with contextlib.chdir(working_dir):
        success, output = run(
            [
                "cmake",
                "--build",
                "--preset",
                f"{preset.build}",
                "--target",
                "install",
                "--config",
                f"{config}",
            ]
        )
        if not success:
            if output is not None:
                print(output)

            return False

    return True


def dir_from_preset(dir_key, preset, cmake_source_dir) -> str:
    preset_name = preset if isinstance(preset, str) else preset.configure

    presets_path = os.path.realpath(f"{cmake_source_dir}/CMakePresets.json")
    with open(presets_path) as f:
        data = json.load(f)
        configure_presets = [
            p for p in data["configurePresets"] if p["name"] == preset_name
        ]
        assert len(configure_presets) == 1
        configure_preset = configure_presets[0]

        dir_path = configure_preset[dir_key]
        dir_path = dir_path.replace("${sourceDir}", f"{cmake_source_dir}")

        return os.path.realpath(dir_path)


def cache_var_from_preset(var_name, preset, cmake_source_dir) -> str:
    preset_name = preset if isinstance(preset, str) else preset.configure

    presets_path = os.path.realpath(f"{cmake_source_dir}/CMakePresets.json")
    with open(presets_path) as f:
        data = json.load(f)
        configure_presets = [
            p for p in data["configurePresets"] if p["name"] == preset_name
        ]
        assert len(configure_presets) == 1
        configure_preset = configure_presets[0]

        cache_vars = configure_preset["cacheVariables"]

        return cache_vars[var_name]


def build_dir_from_preset(preset, cmake_source_dir) -> str:
    return dir_from_preset("binaryDir", preset, cmake_source_dir)


def install_dir_from_preset(preset, cmake_source_dir) -> str:
    return dir_from_preset("installDir", preset, cmake_source_dir)


def clean_build_dir(preset, cmake_source_dir):
    build_dir = build_dir_from_preset(preset, cmake_source_dir)
    remove_dir(build_dir)


def clean_install_dir(preset, cmake_source_dir):
    install_dir = install_dir_from_preset(preset, cmake_source_dir)
    remove_dir(install_dir)


def copy_install_dir(preset, cmake_source_dir, destination):
    remove_dir(destination)
    install_dir = install_dir_from_preset(preset, cmake_source_dir)
    recursively_copy_dir(install_dir, destination)


def run_target(
    preset, cmake_source_dir, build_config, target
) -> typing.Tuple[bool, str | None]:
    with contextlib.chdir(cmake_source_dir):
        build_dir = build_dir_from_preset(preset, cmake_source_dir)

        return run([f"{build_dir}/{build_config}/{target}"])
