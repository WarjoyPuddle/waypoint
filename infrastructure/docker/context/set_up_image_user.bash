# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

set -euo pipefail

function main
{
  mkdir --parents \
    "${HOME}/.local/bin"
  go install mvdan.cc/sh/v3/cmd/shfmt@v3.12.0
}

main
