// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#pragma once

#include "waypoint/waypoint.hpp"

#include <algorithm>
// NOLINTNEXTLINE(misc-include-cleaner)
#include <cstring>
#include <format>
#include <functional>
// NOLINTNEXTLINE(misc-include-cleaner)
#include <iostream>
#include <optional>
#include <string>
#include <utility>

namespace waypoint::test
{

class CopyableImmovable
{
public:
  ~CopyableImmovable() = default;
  CopyableImmovable() = default;
  CopyableImmovable(CopyableImmovable const &other) = default;
  CopyableImmovable(CopyableImmovable &&other) noexcept = delete;
  auto operator=(CopyableImmovable const &other)
    -> CopyableImmovable & = default;
  auto operator=(CopyableImmovable &&other) noexcept
    -> CopyableImmovable & = delete;

  // NOLINTNEXTLINE(google-explicit-constructor)
  operator int() const
  {
    return this->foo;
  }

  int foo{42};
};

struct X
{
  // NOLINTNEXTLINE(google-explicit-constructor)
  operator int() const
  {
    return this->foo;
  }

  int foo;
};

constexpr inline int x_init = 1'000'000;
extern int x;

inline auto void_setup_factory(int const new_x)
{
  return [new_x](waypoint::Context const &ctx)
  {
    ctx.assert(waypoint::test::x == waypoint::test::x_init);

    waypoint::test::x = new_x;
  };
}

inline auto body_factory_no_fixture(int const expected_x, int const new_x)
{
  return [expected_x, new_x](waypoint::Context const &ctx)
  {
    ctx.assert(waypoint::test::x == expected_x);

    waypoint::test::x = new_x;
  };
}

template<typename T>
auto setup_factory_fixture(int const fixture_, int const new_x)
{
  return [fixture_, new_x](waypoint::Context const &ctx)
  {
    ctx.assert(waypoint::test::x == waypoint::test::x_init);

    waypoint::test::x = new_x;

    return T{fixture_};
  };
}

template<typename T>
auto body_factory_fixture(
  int const new_x,
  int const fixture_expected,
  int const x_expected)
{
  return [new_x,
          fixture_expected,
          x_expected](waypoint::Context const &ctx, T const &fixture)
  {
    ctx.assert(x_expected == waypoint::test::x);
    ctx.assert(fixture_expected == fixture);

    waypoint::test::x = new_x;
  };
}

void trivial_test_setup(waypoint::Context const &ctx);
void trivial_test_body(waypoint::Context const &ctx);
void trivial_failing_body(waypoint::Context const &ctx);
void trivial_test_teardown(waypoint::Context const &ctx);
void increment_x_test_body(waypoint::Context const &ctx);

auto int_fixture_test_setup(waypoint::Context const &ctx) -> int;
void int_fixture_test_body(waypoint::Context const &ctx, int const &fixture);
void int_fixture_increment_x_test_body(
  waypoint::Context const &ctx,
  int const &fixture);
void int_fixture_teardown(waypoint::Context const &ctx, int const &fixture);

auto get_env(std::string const &var_name) -> std::optional<std::string>;

void body_short_sleep(waypoint::Context const &ctx) noexcept;
void body_long_sleep(waypoint::Context const &ctx) noexcept;
void int_fixture_body_long_sleep(
  waypoint::Context const &ctx,
  int const &fixture) noexcept;

void body_call_std_exit_123(waypoint::Context const &ctx);
void body_call_std_abort(waypoint::Context const &ctx);
void body_failing_assertion(waypoint::Context const &ctx);
void body_throws_exception(waypoint::Context const &ctx);
void body_throws_exception_while_noexcept(
  waypoint::Context const &ctx) noexcept;

} // namespace waypoint::test

namespace std
{

template<>
struct formatter<waypoint::TestOutcome::Status, char>
{
  template<class ParseContext>
  constexpr auto parse(ParseContext &ctx) -> ParseContext::iterator
  {
    return ctx.end();
  }

  template<class FormatContext>
  auto format(waypoint::TestOutcome::Status status, FormatContext &ctx) const
    -> FormatContext::iterator
  {
    std::string out = std::invoke(
      [status]()
      {
        switch(status)
        {
        case waypoint::TestOutcome::Status::Failure:
          return "Failure";
        case waypoint::TestOutcome::Status::NotRun:
          return "NotRun";
        case waypoint::TestOutcome::Status::Success:
          return "Success";
        case waypoint::TestOutcome::Status::Terminated:
          return "Terminated";
        case waypoint::TestOutcome::Status::Timeout:
          return "Timeout";
        }

        std::unreachable();
      });

    return std::ranges::copy(std::move(out), ctx.out()).out;
  }
};

} // namespace std

#define REQUIRE_IN_MAIN(condition, message) \
  if(!(condition)) \
  { \
    std::cerr << (message) << std::endl; \
    return 1; \
  }

#define REQUIRE_STRING_EQUAL_IN_MAIN(str1, str2, message) \
  REQUIRE_IN_MAIN((std::strcmp((str1), (str2)) == 0), (message))
