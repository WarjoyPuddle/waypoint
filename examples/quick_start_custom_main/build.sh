#!/bin/bash
# Copyright (c) 2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

set -euo pipefail

main()
{
  # Configure step
  cmake --preset configure

  # Build step
  cmake --build --preset build --config Debug

  # Run the tests with CMake
  cmake --build --preset build --target test --config Debug

  # Alternatively, run the tests with CTest (a more flexible approach)
  ctest --preset test --build-config Debug

  # You may also run the test executable directly
  build___/Debug/test_program

  # Demonstrate that custom main function is actually in use
  if build___/Debug/test_program | grep "oCbUUvaK8qju51I9" >/dev/null 2>&1;
  then
    echo "Correct entry point found"
  else
    echo "Error: Incorrect entry point"
    exit 1
  fi

  echo "Success: $(basename "$0")"
}

main
