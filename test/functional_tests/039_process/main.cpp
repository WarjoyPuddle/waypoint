// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "test_helpers/test_helpers.hpp"
#include "waypoint/waypoint.hpp"

#include <format>
#include <vector>

WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g1 = t.group("Test group 1");

  t.test(g1, "Test 1")
    .run(
      [](auto const &ctx)
      {
        if(!ctx.assert(true) || ctx.assert(true, "body assertion message"))
        {
        }
      });
  t.test(g1, "Test 2").run(waypoint::test::trivial_test_body);
  t.test(g1, "Test 3").run(waypoint::test::trivial_test_body);
  t.test(g1, "Test 4").run(waypoint::test::trivial_failing_body);
  t.test(g1, "Test 5").run(waypoint::test::trivial_test_body);
  t.test(g1, "Test 6").run(waypoint::test::trivial_test_body).disable();
}

auto main() -> int
{
  auto const t = waypoint::TestRun::create();

  auto const results = waypoint::run_all_tests(t);

  REQUIRE_IN_MAIN(!results.success(), "Expected the run to fail");
  auto const error_count = results.error_count();
  REQUIRE_IN_MAIN(
    error_count == 0,
    std::format("Expected error_count to be 0, but it is {}", error_count));

  auto const test_count = results.test_count();
  REQUIRE_IN_MAIN(
    test_count == 6,
    std::format("Expected test_count to be 6, but it is {}", test_count));

  std::vector const statuses{
    waypoint::TestOutcome::Status::Success,
    waypoint::TestOutcome::Status::Success,
    waypoint::TestOutcome::Status::Success,
    waypoint::TestOutcome::Status::Failure,
    waypoint::TestOutcome::Status::Success,
    waypoint::TestOutcome::Status::NotRun};

  for(unsigned i = 0; i < test_count; ++i)
  {
    auto const &test_outcome = results.test_outcome(i);
    auto const expected_status = statuses[i];
    auto const actual_status = test_outcome.status();
    REQUIRE_IN_MAIN(
      actual_status == expected_status,
      std::vformat(
        "Expected actual_status to be {}, but it is {}",
        std::make_format_args(expected_status, actual_status)));
    if(expected_status == waypoint::TestOutcome::Status::Success)
    {
      REQUIRE_IN_MAIN(
        !test_outcome.disabled(),
        "Expected test_outcome.disabled() to be false");
      REQUIRE_IN_MAIN(
        test_outcome.assertion_count() == 2,
        std::format(
          "Expected test_outcome.assertion_count() to be 2, but it is {}",
          test_outcome.assertion_count()));
      auto const &assertion_outcome1 = test_outcome.assertion_outcome(0);
      REQUIRE_IN_MAIN(
        assertion_outcome1.passed(),
        "Expected assertion_outcome1.passed() to be true");
      REQUIRE_IN_MAIN(
        assertion_outcome1.message() == nullptr,
        "Expected assertion_outcome1.message() == nullptr");
      auto const &assertion_outcome2 = test_outcome.assertion_outcome(1);
      REQUIRE_IN_MAIN(
        assertion_outcome2.passed(),
        "Expected assertion_outcome2.passed() to be true");
      REQUIRE_STRING_EQUAL_IN_MAIN(
        assertion_outcome2.message(),
        "body assertion message",
        std::format(
          "Unexpected string value: {}",
          assertion_outcome2.message()));
    }
    else if(expected_status == waypoint::TestOutcome::Status::Failure)
    {
      REQUIRE_IN_MAIN(
        !test_outcome.disabled(),
        "Expected test_outcome.disabled() to be false");
      REQUIRE_IN_MAIN(
        test_outcome.assertion_count() == 2,
        std::format(
          "Expected test_outcome.assertion_count() to be 2, but it is {}",
          test_outcome.assertion_count()));
      auto const &assertion_outcome1 = test_outcome.assertion_outcome(0);
      REQUIRE_IN_MAIN(
        !assertion_outcome1.passed(),
        "Expected assertion_outcome1.passed() to be false");
      REQUIRE_IN_MAIN(
        assertion_outcome1.message() == nullptr,
        "Expected assertion_outcome1.message() == nullptr");
      auto const &assertion_outcome2 = test_outcome.assertion_outcome(1);
      REQUIRE_IN_MAIN(
        !assertion_outcome2.passed(),
        "Expected assertion_outcome2.passed() to be false");
      REQUIRE_STRING_EQUAL_IN_MAIN(
        assertion_outcome2.message(),
        "failing body assertion message",
        std::format(
          "Unexpected string value: {}",
          assertion_outcome2.message()));
    }
    else if(expected_status == waypoint::TestOutcome::Status::NotRun)
    {
      REQUIRE_IN_MAIN(
        test_outcome.disabled(),
        "Expected test_outcome.disabled() to be true");
      REQUIRE_IN_MAIN(
        test_outcome.assertion_count() == 0,
        std::format(
          "Expected test_outcome.assertion_count() to be 0, but it was {}",
          test_outcome.assertion_count()));
    }
  }

  return 0;
}
