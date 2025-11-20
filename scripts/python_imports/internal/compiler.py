# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import enum


@enum.unique
class Compiler(enum.Enum):
    Clang = 0
    Gcc = 1
