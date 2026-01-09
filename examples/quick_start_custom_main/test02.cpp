// Copyright (c) 2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "the_answer.hpp"

#include "waypoint/waypoint.hpp"

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g = t.group("the_answer tests");

  t.test(g, "two answers are better than one")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(
          2 * deep_thought::the_answer() > deep_thought::the_answer(),
          "two answers are better than one");
      });
}
