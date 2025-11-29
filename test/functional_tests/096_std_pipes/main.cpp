// Copyright (c) 2025 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "waypoint/waypoint.hpp"

#include <iostream>

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g = t.group("Test group");

  t.test(g, "Test 1")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cout << "a1" << std::endl;
        ctx.assert(true);
        std::cout << "a2" << std::endl;
      });

  t.test(g, "Test 2")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cout << "a3" << std::endl;
        ctx.assert(true);
        std::cerr << "a4" << std::endl;
      });

  t.test(g, "Test 3")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cerr << "a5" << std::endl;
        ctx.assert(true);
        std::cout << "a6" << std::endl;
      });

  t.test(g, "Test 4")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cerr << "a7" << std::endl;
        ctx.assert(true);
        std::cerr << "a8" << std::endl;
      });

  t.test(g, "Test 5")
    .run(
      [](waypoint::Context const &ctx)
      {
        std::cout << "a9" << std::endl;
        std::cerr << "a10" << std::endl;
        ctx.assert(true);
        std::cout << "a11" << std::endl;
        std::cerr << "a12" << std::endl;
      });
}

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results = waypoint::run_all_tests(t);
  if(!results.success())
  {
    std::cerr << "Expected the run to succeed" << std::endl;

    return 1;
  }

  return 0;
}
