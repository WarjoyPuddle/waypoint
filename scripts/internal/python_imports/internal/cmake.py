# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import contextlib
import json
import os
import pathlib

from .process import run
from .system import get_cpu_count
from .system import new_env
from .system import recursively_copy_dir
from .system import remove_dir

CLANG_ENV_PATCH = {"CC": "clang-20", "CXX": "clang++-20"}


@contextlib.contextmanager
def clang():
    env = os.environ.copy()
    env.update(CLANG_ENV_PATCH)
    with new_env(env):
        try:
            yield None
        finally:
            pass


def configure_cmake(preset, cmake_source_dir: pathlib.Path) -> bool:
    build_dir = build_dir_from_preset(preset, cmake_source_dir)

    if build_dir.exists():
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


def build_cmake(config, preset, cmake_source_dir: pathlib.Path, target) -> bool:
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


def run_ctest(
    preset, build_config, label_include_regex, cmake_source_dir: pathlib.Path
) -> bool:
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


def install_cmake(preset, config, working_dir: pathlib.Path) -> bool:
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


def dir_from_preset(dir_key, preset, cmake_source_dir: pathlib.Path) -> pathlib.Path:
    preset_name = preset if isinstance(preset, str) else preset.configure

    presets_path = (cmake_source_dir / "CMakePresets.json").resolve()
    with open(presets_path, "r") as f:
        data = json.load(f)
        configure_presets = [
            p for p in data["configurePresets"] if p["name"] == preset_name
        ]
        assert len(configure_presets) == 1
        configure_preset = configure_presets[0]

        dir_path = configure_preset[dir_key]
        dir_path = dir_path.replace("${sourceDir}", str(cmake_source_dir))

        return pathlib.Path(dir_path).resolve()


def cache_var_from_preset(var_name, preset, cmake_source_dir: pathlib.Path) -> str:
    preset_name = preset if isinstance(preset, str) else preset.configure

    presets_path = (cmake_source_dir / "CMakePresets.json").resolve()
    with open(presets_path, "r") as f:
        data = json.load(f)
        configure_presets = [
            p for p in data["configurePresets"] if p["name"] == preset_name
        ]
        assert len(configure_presets) == 1
        configure_preset = configure_presets[0]

        cache_vars = configure_preset["cacheVariables"]

        return cache_vars[var_name]


def build_dir_from_preset(preset, cmake_source_dir: pathlib.Path) -> pathlib.Path:
    return dir_from_preset("binaryDir", preset, cmake_source_dir)


def install_dir_from_preset(preset, cmake_source_dir: pathlib.Path) -> pathlib.Path:
    return dir_from_preset("installDir", preset, cmake_source_dir)


def clean_build_dir(preset, cmake_source_dir: pathlib.Path):
    build_dir = build_dir_from_preset(preset, cmake_source_dir)
    remove_dir(build_dir)


def clean_install_dir(preset, cmake_source_dir: pathlib.Path):
    install_dir = install_dir_from_preset(preset, cmake_source_dir)
    remove_dir(install_dir)


def copy_install_dir(preset, cmake_source_dir: pathlib.Path, destination: pathlib.Path):
    remove_dir(destination)
    install_dir = install_dir_from_preset(preset, cmake_source_dir)
    recursively_copy_dir(install_dir, destination)


def run_target(
    preset, cmake_source_dir: pathlib.Path, build_config, target
) -> tuple[bool, str | None]:
    with contextlib.chdir(cmake_source_dir):
        build_dir = build_dir_from_preset(preset, cmake_source_dir)

        return run([f"{build_dir}/{build_config}/{target}"])
