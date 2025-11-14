# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import json
import os

from .compiler import Compiler
from .process import run
from .system import NewEnv
from .system import get_cpu_count
from .system import remove_dir

CLANG20_ENV_PATCH = {"CC": "clang-20", "CXX": "clang++-20"}
GCC15_ENV_PATCH = {"CC": "gcc-15", "CXX": "g++-15"}


def env_patch_from_reset(preset):
    if preset.compiler == Compiler.Clang:
        return CLANG20_ENV_PATCH
    if preset.compiler == Compiler.Gcc:
        return GCC15_ENV_PATCH

    assert False, "Unreachable"


def configure_cmake(preset, cmake_source_dir) -> bool:
    env_patch = env_patch_from_reset(preset)

    env = os.environ.copy()
    env.update(env_patch)
    with NewEnv(env):
        build_dir = build_dir_from_preset(preset, cmake_source_dir)

        if os.path.exists(build_dir):
            return True

        os.mkdir(build_dir)

        with contextlib.chdir(cmake_source_dir):
            command = ["cmake", "--preset", f"{preset.configure}"]
            success, output = run(command)
            if not success:
                if output is not None:
                    print(output)

                return False

    return True


def build_cmake(config, preset, cmake_source_dir, target) -> bool:
    env_patch = env_patch_from_reset(preset)

    env = os.environ.copy()
    env.update(env_patch)
    with NewEnv(env):
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
    presets_path = os.path.realpath(f"{cmake_source_dir}/CMakePresets.json")
    with open(presets_path) as f:
        data = json.load(f)
        configure_presets = [
            p for p in data["configurePresets"] if p["name"] == preset.configure
        ]
        assert len(configure_presets) == 1
        configure_presets = configure_presets[0]

        dir_path = configure_presets[dir_key]
        dir_path = dir_path.replace("${sourceDir}", f"{cmake_source_dir}")

        return os.path.realpath(dir_path)


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
