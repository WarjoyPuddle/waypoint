# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file


import hashlib
import os
import subprocess

from .system import get_python

PRE_COMMIT_HOOK_DIGEST = (
    "f8c383806649c4bf8f5f8342b6ea66365d180656c2067bb7c471f72dd76773f2"
)
POST_COMMIT_HOOK_DIGEST = (
    "5144a04dadd4f98c4c93233665bb30646ebd7850a17eb2dcc42b2988474a8328"
)
POST_CHECKOUT_HOOK_DIGEST = (
    "e220e9b10371ad71cacb8b4ff9425294214e63cf40b538f9cb3e61adc2c43781"
)


def git_dir_path(project_root_dir: str) -> str:
    return os.path.realpath(f"{project_root_dir}/.git")


def pre_commit_hook_path(git_dir: str) -> str:
    return os.path.realpath(f"{git_dir}/hooks/pre-commit")


def post_commit_hook_path(git_dir: str) -> str:
    return os.path.realpath(f"{git_dir}/hooks/post-commit")


def post_checkout_hook_path(git_dir: str) -> str:
    return os.path.realpath(f"{git_dir}/hooks/post-checkout")


def install_hooks_script_path(project_root_dir: str) -> str:
    return os.path.realpath(f"{project_root_dir}/scripts/internal/install_hooks.py")


def digest_equals(path: str, expected_digest: str) -> bool:
    with open(path, "br") as f:
        data = f.read()

    sha3_256 = hashlib.sha3_256()
    sha3_256.update(data)
    sha3_256_digest = sha3_256.hexdigest()

    return sha3_256_digest == expected_digest


def ensure_hooks_installed(project_root_dir: str) -> bool:
    git_dir = git_dir_path(project_root_dir)

    if (
        os.path.isfile(pre_commit_hook_path(git_dir))
        and os.path.isfile(post_commit_hook_path(git_dir))
        and os.path.isfile(post_commit_hook_path(git_dir))
        and digest_equals(pre_commit_hook_path(git_dir), PRE_COMMIT_HOOK_DIGEST)
        and digest_equals(post_commit_hook_path(git_dir), POST_COMMIT_HOOK_DIGEST)
        and digest_equals(post_checkout_hook_path(git_dir), POST_CHECKOUT_HOOK_DIGEST)
    ):
        return True

    result = subprocess.run([get_python(), install_hooks_script_path(project_root_dir)])
    assert result.returncode == 0

    if (
        not digest_equals(pre_commit_hook_path(git_dir), PRE_COMMIT_HOOK_DIGEST)
        or not digest_equals(post_commit_hook_path(git_dir), POST_COMMIT_HOOK_DIGEST)
        or not digest_equals(
            post_checkout_hook_path(git_dir), POST_CHECKOUT_HOOK_DIGEST
        )
    ):
        print(
            f"Error: Unexpected hook digest values: update {os.path.basename(__file__)}"
        )

        return False

    return True


def download_dependencies() -> None:
    pass


def build_tools() -> None:
    pass
