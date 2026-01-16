// Copyright (c) 2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "waypoint/waypoint.hpp"

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results = waypoint::run_all_tests(t);

  if(results.error_count() > 0)
  {
    return 1;
  }

  if(!results.success())
  {
    return 1;
  }

  return 0;
}
