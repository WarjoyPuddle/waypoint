// Copyright (c) 2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "the_answer.hpp"

#include "waypoint/waypoint.hpp"

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g = t.group("the_answer tests");

  t.test(g, "the_answer() returns the correct value")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(
          deep_thought::the_answer() == 42,
          "the_answer() should return 42");
      });

  t.test(g, "the_answer() does not return an incorrect value")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(
          deep_thought::the_answer() != 69,
          "the_answer() should return 42");
      });
}
