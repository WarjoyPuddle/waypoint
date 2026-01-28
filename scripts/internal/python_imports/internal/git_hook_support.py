# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file


import hashlib
import pathlib
import subprocess

from .system import get_python

PRE_COMMIT_HOOK_DIGEST = (
    "a0ea155d8cc69c4328ef797b1fd6c5d00e41d759bdf5cdf745a63b4c2d5bbad0"
)
POST_COMMIT_HOOK_DIGEST = (
    "fad2aad70624769788b0d54fa73e4d258299d16a60e2442a5ce89b703c4190b6"
)
POST_CHECKOUT_HOOK_DIGEST = (
    "07b15489dcce8e6b5a47a08f5abe10ace07261bbf86bdd038f6c9155fbfeba3e"
)


def git_dir_path(project_root_dir: pathlib.Path) -> pathlib.Path:
    return project_root_dir / ".git"


def pre_commit_hook_path(git_dir: pathlib.Path) -> pathlib.Path:
    return git_dir / "hooks/pre-commit"


def post_commit_hook_path(git_dir: pathlib.Path) -> pathlib.Path:
    return git_dir / "hooks/post-commit"


def post_checkout_hook_path(git_dir: pathlib.Path) -> pathlib.Path:
    return git_dir / "hooks/post-checkout"


def install_hooks_script_path(project_root_dir: pathlib.Path) -> pathlib.Path:
    path = project_root_dir / "scripts/internal/install_hooks.py"

    assert path.is_file()

    return path


def digest(path: pathlib.Path) -> str:
    with open(path, "br") as f:
        data = f.read()

    sha3_256 = hashlib.sha3_256()
    sha3_256.update(data)
    sha3_256_digest = sha3_256.hexdigest()

    return sha3_256_digest


def ensure_hooks_installed(project_root_dir: pathlib.Path) -> bool:
    git_dir = git_dir_path(project_root_dir)

    pre_commit_hook = pre_commit_hook_path(git_dir)
    post_commit_hook = post_commit_hook_path(git_dir)
    post_checkout_hook = post_checkout_hook_path(git_dir)

    pre_commit_hook_digest = digest(pre_commit_hook)
    post_commit_hook_digest = digest(post_commit_hook)
    post_checkout_hook_digest = digest(post_checkout_hook)
    if (
        pre_commit_hook.is_file()
        and post_commit_hook.is_file()
        and post_checkout_hook.is_file()
        and pre_commit_hook_digest == PRE_COMMIT_HOOK_DIGEST
        and post_commit_hook_digest == POST_COMMIT_HOOK_DIGEST
        and post_checkout_hook_digest == POST_CHECKOUT_HOOK_DIGEST
    ):
        return True

    result = subprocess.run(
        [get_python(), str(install_hooks_script_path(project_root_dir))]
    )
    assert result.returncode == 0

    if (
        pre_commit_hook_digest != PRE_COMMIT_HOOK_DIGEST
        or post_commit_hook_digest != POST_COMMIT_HOOK_DIGEST
        or post_checkout_hook_digest != POST_CHECKOUT_HOOK_DIGEST
    ):
        print(
            f"Error: Unexpected hook digest values: update {pathlib.Path(__file__).name}"
        )
        print(f"PRE_COMMIT_HOOK_DIGEST = {pre_commit_hook_digest}")
        print(f"POST_COMMIT_HOOK_DIGEST = {post_commit_hook_digest}")
        print(f"POST_CHECKOUT_HOOK_DIGEST = {post_checkout_hook_digest}")

        return False

    return True


def download_dependencies() -> None:
    pass


def build_tools() -> None:
    pass
