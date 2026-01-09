// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "waypoint.hpp"

#include <utility>

namespace waypoint::internal
{

Registrar<void>::~Registrar()
{
  if(!this->is_active_)
  {
    return;
  }

  if(!static_cast<bool>(this->body_))
  {
    this->report_incomplete_test(this->test_id_);

    return;
  }

  this->test_run_.register_test_assembly(
    [setup = std::move(this->setup_),
     body = std::move(this->body_),
     teardown = std::move(this->teardown_)](Context const &ctx) noexcept
    {
      if(static_cast<bool>(setup))
      {
        setup(ctx);
      }
      body(ctx);
      if(static_cast<bool>(teardown))
      {
        teardown(ctx);
      }
    },
    this->test_id_,
    this->timeout_ms_,
    this->is_disabled_);
}

Registrar<void>::Registrar(Registrar &&other) noexcept
  : is_active_{other.is_active_},
    test_run_{other.test_run_},
    test_id_{other.test_id_},
    timeout_ms_{other.timeout_ms_},
    setup_{std::move(other.setup_)},
    body_{std::move(other.body_)},
    teardown_{std::move(other.teardown_)},
    is_disabled_{false}
{
  other.is_active_ = false;
}

void Registrar<void>::register_setup(VoidSetup f)
{
  this->is_active_ = true;

  this->setup_ = std::move(f);
}

void Registrar<void>::register_body(TestBodyNoFixture f)
{
  this->is_active_ = true;

  this->body_ = std::move(f);
}

void Registrar<void>::register_teardown(TeardownNoFixture f)
{
  this->is_active_ = true;

  this->teardown_ = std::move(f);
}

void Registrar<void>::set_timeout_ms(unsigned long long const timeout_ms)
{
  this->timeout_ms_ = timeout_ms;
}

void Registrar<void>::disable(bool const is_disabled)
{
  this->is_disabled_ = is_disabled;
}

Registrar<void>::Registrar(
  TestRun const &test_run,
  unsigned long long const test_id)
  : is_active_{false},
    test_run_{test_run},
    test_id_{test_id},
    timeout_ms_{DEFAULT_TIMEOUT_MS},
    is_disabled_{false}
{
}

void Registrar<void>::report_incomplete_test(
  unsigned long long const test_id) const
{
  this->test_run_.report_incomplete_test(test_id);
}

} // namespace waypoint::internal
