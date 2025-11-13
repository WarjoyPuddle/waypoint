# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import subprocess
import tempfile
import typing


def run(cmd) -> typing.Tuple[bool, str | None]:
    with tempfile.TemporaryFile("r+") as f:
        try:
            result = subprocess.run(cmd, stdout=f, stderr=f)
        except FileNotFoundError:
            return False, None

        output = "\n"
        f.seek(0)
        output += f.read()
        output += "\n"

        return (result.returncode == 0), output
