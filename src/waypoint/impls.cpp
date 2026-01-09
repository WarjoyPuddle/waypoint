// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "impls.hpp"

#include "types.hpp"
#include "waypoint.hpp"

#include "process/process.hpp"

#include <algorithm>
#include <cstdint>
#include <format>
#include <functional>
#include <iterator>
#include <memory>
#include <mutex>
#include <optional>
#include <random>
#include <ranges>
#include <string>
#include <utility>
#include <vector>

namespace waypoint::internal
{

AssertionOutcome_impl::AssertionOutcome_impl()
  : test_outcome_{},
    passed_{},
    index_{}
{
}

void AssertionOutcome_impl::initialize(
  TestOutcome const *const test_outcome,
  std::optional<std::string> message,
  bool const passed,
  unsigned long long const index)
{
  this->test_outcome_ = test_outcome;
  this->message_ = std::move(message);
  this->passed_ = passed;
  this->index_ = index;
}

auto AssertionOutcome_impl::group_name() const -> char const *
{
  return this->test_outcome_->group_name();
}

auto AssertionOutcome_impl::test_name() const -> char const *
{
  return this->test_outcome_->test_name();
}

auto AssertionOutcome_impl::message() const
  -> std::optional<std::string> const &
{
  return this->message_;
}

auto AssertionOutcome_impl::passed() const -> bool
{
  return this->passed_;
}

auto AssertionOutcome_impl::index() const -> unsigned long long
{
  return this->index_;
}

TestOutcome_impl::TestOutcome_impl()
  : test_index_{},
    disabled_{},
    status_{TestOutcome::Status::NotRun}
{
}

void TestOutcome_impl::initialize(
  std::vector<std::unique_ptr<AssertionOutcome>> assertion_outcomes,
  std::string group_name,
  std::string test_name,
  unsigned long long const index,
  bool const disabled,
  TestOutcome::Status const status,
  std::optional<unsigned long long> const maybe_exit_status,
  std::string &&std_out,
  std::string &&std_err)
{
  this->assertion_outcomes_ = std::move(assertion_outcomes);
  this->group_name_ = std::move(group_name);
  this->test_name_ = std::move(test_name);
  this->test_index_ = index;
  this->disabled_ = disabled;
  this->status_ = status;
  this->exit_status_ = maybe_exit_status;
  this->std_out_ = std::move(std_out);
  this->std_err_ = std::move(std_err);
}

auto TestOutcome_impl::get_test_name() const -> std::string const &
{
  return this->test_name_;
}

auto TestOutcome_impl::get_group_name() const -> std::string const &
{
  return this->group_name_;
}

auto TestOutcome_impl::get_assertion_count() const -> unsigned long long
{
  return this->assertion_outcomes_.size();
}

auto TestOutcome_impl::get_assertion_outcome(
  unsigned long long const index) const -> AssertionOutcome const &
{
  return *this->assertion_outcomes_[index];
}

auto TestOutcome_impl::get_index() const -> unsigned long long
{
  return this->test_index_;
}

auto TestOutcome_impl::disabled() const -> bool
{
  return this->disabled_;
}

auto TestOutcome_impl::status() const -> TestOutcome::Status
{
  return this->status_;
}

auto TestOutcome_impl::exit_status() const
  -> std::optional<unsigned long long> const &
{
  return this->exit_status_;
}

auto TestOutcome_impl::std_out() const -> std::string const &
{
  return this->std_out_;
}

auto TestOutcome_impl::std_err() const -> std::string const &
{
  return this->std_err_;
}

TestRecord::TestRecord(
  TestAssembly assembly,
  TestId const test_id,
  unsigned long long const timeout_ms,
  bool const disabled)
  : test_assembly_(std::move(assembly)),
    test_id_{test_id},
    disabled_{disabled},
    status_{TestRecord::Status::NotRun},
    timeout_ms_{timeout_ms}
{
}

auto TestRecord::test_id() const -> TestId
{
  return this->test_id_;
}

auto TestRecord::test_assembly() const -> TestAssembly const &
{
  return this->test_assembly_;
}

auto TestRecord::disabled() const -> bool
{
  return this->disabled_;
}

auto TestRecord::status() const -> TestRecord::Status
{
  return this->status_;
}

auto TestRecord::timeout_ms() const -> unsigned long long
{
  return this->timeout_ms_;
}

void TestRecord::mark_as_run()
{
  this->status_ = TestRecord::Status::Complete;
}

void TestRecord::mark_as_crashed()
{
  this->status_ = TestRecord::Status::Terminated;
}

void TestRecord::mark_as_timed_out()
{
  this->status_ = TestRecord::Status::Timeout;
}

void TestRecord::append_std_output(std::string const &text)
{
  this->std_out_ << text;
}

void TestRecord::append_std_error(std::string const &text)
{
  this->std_err_ << text;
}

auto TestRecord::get_std_out() const -> std::string
{
  return this->std_out_.str();
}

auto TestRecord::get_std_err() const -> std::string
{
  return this->std_err_.str();
}

AssertionRecord::AssertionRecord(
  bool const condition,
  AssertionIndex const index,
  std::optional<std::string> maybe_message)
  : condition_{condition},
    index_{index},
    maybe_message_{std::move(maybe_message)}
{
}

auto AssertionRecord::passed() const -> bool
{
  return this->condition_;
}

auto AssertionRecord::index() const -> AssertionIndex
{
  return this->index_;
}

auto AssertionRecord::message() const -> std::optional<std::string>
{
  return this->maybe_message_;
}

Group_impl::Group_impl()
  : id_{}
{
}

void Group_impl::set_id(GroupId const id)
{
  this->id_ = id;
}

auto Group_impl::get_id() const -> GroupId
{
  return this->id_;
}

Test_impl::~Test_impl()
{
  if(incomplete_ && this->test_run_ != nullptr)
  {
    get_impl(*this->test_run_).report_incomplete_test(this->id_);
  }
}

Test_impl::Test_impl()
  : test_run_{},
    id_{},
    incomplete_{true}
{
}

void Test_impl::initialize(TestRun const &test_run, TestId const id)
{
  this->test_run_ = &test_run;
  this->id_ = id;
}

auto Test_impl::get_test_run() const -> TestRun const &
{
  return *test_run_;
}

auto Test_impl::get_id() const -> TestId
{
  return this->id_;
}

void Test_impl::mark_complete()
{
  this->incomplete_ = false;
}

ContextInProcess_impl::ContextInProcess_impl()
  : test_run_{},
    test_id_{},
    assertion_index_{}
{
}

void ContextInProcess_impl::initialize(
  TestRun const &test_run,
  TestId const test_id)
{
  this->test_run_ = &test_run;
  this->test_id_ = test_id;
  this->assertion_index_ = 0;
}

auto ContextInProcess_impl::get_test_run() const -> TestRun const &
{
  return *test_run_;
}

auto ContextInProcess_impl::generate_assertion_index() -> AssertionIndex
{
  return assertion_index_++;
}

auto ContextInProcess_impl::test_id() const -> TestId
{
  return this->test_id_;
}

ContextChildProcess_impl::ContextChildProcess_impl()
  : test_run_{},
    test_id_{},
    assertion_index_{},
    response_write_pipe_{},
    transmission_mutex_{}
{
}

void ContextChildProcess_impl::initialize(
  TestRun const &test_run,
  TestId const test_id,
  InputPipeEnd const &response_write_pipe,
  std::mutex &transmission_mutex)
{
  this->test_run_ = &test_run;
  this->test_id_ = test_id;
  this->assertion_index_ = 0;
  this->response_write_pipe_ = &response_write_pipe;
  this->transmission_mutex_ = &transmission_mutex;
}

auto ContextChildProcess_impl::get_test_run() const -> TestRun const &
{
  return *test_run_;
}

auto ContextChildProcess_impl::generate_assertion_index() -> AssertionIndex
{
  return assertion_index_++;
}

auto ContextChildProcess_impl::test_id() const -> TestId
{
  return this->test_id_;
}

auto ContextChildProcess_impl::response_write_pipe() const
  -> InputPipeEnd const *
{
  return this->response_write_pipe_;
}

auto ContextChildProcess_impl::transmission_mutex() const -> std::mutex *
{
  return this->transmission_mutex_;
}

TestRun_impl::TestRun_impl()
  : test_run_{nullptr},
    group_id_counter_{0},
    test_id_counter_{0}
{
}

auto TestRun_impl::make_group(GroupId const group_id) const -> Group
{
  auto *impl = new Group_impl{};

  impl->set_id(group_id);

  return Group{impl};
}

auto TestRun_impl::make_test(TestId const test_id) const -> Test
{
  auto *impl = new Test_impl{};

  impl->initialize(*this->test_run_, test_id);

  return Test{impl};
}

auto TestRun_impl::get_group_id(TestId const id) const -> GroupId
{
  return this->test_id2group_id_.at(id);
}

auto TestRun_impl::get_group_id(Group const &group) const -> GroupId
{
  return group.impl_->get_id();
}

auto TestRun_impl::get_group_name(GroupId const id) const -> std::string
{
  return this->group_id2group_name_.at(id);
}

auto TestRun_impl::get_test_name(TestId const id) const -> std::string
{
  return this->test_id2test_name_.at(id);
}

void TestRun_impl::set_test_index(
  TestId const test_id,
  unsigned long long const index)
{
  this->test_id2test_index_[test_id] = index;
}

auto TestRun_impl::get_test_index(TestId const test_id) const
  -> unsigned long long
{
  return this->test_id2test_index_.at(test_id);
}

auto TestRun_impl::test_count() const -> unsigned long long
{
  return test_id_counter_;
}

auto TestRun_impl::make_test_outcome(TestId const test_id) const noexcept
  -> std::unique_ptr<TestOutcome>
{
  std::vector<std::unique_ptr<AssertionOutcome>> assertion_outcomes;

  auto const assertions = std::invoke(
    [this, test_id]() -> std::vector<AssertionRecord>
    {
      auto const &passing_assertions = this->get_passing_assertions(test_id);
      auto const &failing_assertions = this->get_failing_assertions(test_id);

      auto assertions2 =
        std::ranges::views::join(
          std::vector{passing_assertions, failing_assertions}) |
        std::ranges::to<std::vector<AssertionRecord>>();

      std::ranges::sort(
        assertions2,
        [](auto const &a, auto const &b)
        {
          return a.index() < b.index();
        });

      return assertions2;
    });

  auto *const impl = new TestOutcome_impl{};
  // NOLINTNEXTLINE(clang-analyzer-cplusplus.NewDeleteLeaks)
  auto test_outcome = std::unique_ptr<TestOutcome>(new TestOutcome{impl});

  for(auto const &assertion : assertions)
  {
    auto const maybe_message = assertion.message();
    auto *const assertion_impl = new AssertionOutcome_impl{};

    assertion_impl->initialize(
      test_outcome.get(),
      maybe_message,
      assertion.passed(),
      assertion.index());

    // NOLINTNEXTLINE(clang-analyzer-cplusplus.NewDeleteLeaks)
    assertion_outcomes.emplace_back(
      std::unique_ptr<AssertionOutcome>(new AssertionOutcome{assertion_impl}));
  }

  auto const &test_record = this->test_records_[test_id];

  auto const status = std::invoke(
    [&test_record, &assertion_outcomes]()
    {
      if(test_record.status() == TestRecord::Status::NotRun)
      {
        return TestOutcome::Status::NotRun;
      }

      if(test_record.status() == TestRecord::Status::Terminated)
      {
        return TestOutcome::Status::Terminated;
      }

      if(test_record.status() == TestRecord::Status::Timeout)
      {
        return TestOutcome::Status::Timeout;
      }

      auto const it = std::ranges::find_if(
        assertion_outcomes,
        [](auto const &assertion_outcome)
        {
          return !assertion_outcome->passed();
        });

      return it == assertion_outcomes.end() ? TestOutcome::Status::Success
                                            : TestOutcome::Status::Failure;
    });

  auto std_out = test_record.get_std_out();
  auto std_err = test_record.get_std_err();

  impl->initialize(
    std::move(assertion_outcomes),
    this->get_group_name(this->get_group_id(test_id)),
    this->get_test_name(test_id),
    this->get_test_index(test_id),
    this->is_disabled(test_id),
    status,
    this->get_crashed_exit_status(test_id),
    std::move(std_out),
    std::move(std_err));

  return test_outcome;
}

auto TestRun_impl::register_test(
  GroupId const group_id,
  TestName const &test_name) -> TestId
{
  auto &test_names = test_names_per_group_[group_id];
  if(test_names.contains(test_name))
  {
    auto const &group_name = this->group_id2group_name_[group_id];
    this->report_duplicate_test_name(group_name, test_name);
  }

  test_names.insert(test_name);

  auto const test_id = test_id_counter_++;

  test_id2group_id_[test_id] = group_id;

  this->test_id2test_name_[test_id] = test_name;

  return test_id;
}

auto TestRun_impl::register_group(GroupName const &group_name) -> GroupId
{
  auto const group_id = group_id_counter_++;
  group_id2group_name_[group_id] = group_name;

  return group_id;
}

void TestRun_impl::report_error(ErrorType type, std::string const &message)
{
  this->errors_.emplace_back(type, message);
}

void TestRun_impl::report_duplicate_test_name(
  GroupName const &group_name,
  TestName const &test_name)
{
  this->report_error(
    ErrorType::Init_DuplicateTestInGroup,
    std::format(
      R"(Group "{}" contains duplicate test "{}")",
      group_name,
      test_name));
}

void TestRun_impl::report_incomplete_test(TestId const test_id)
{
  auto const test_name = this->get_test_name(test_id);
  auto const group_id = this->get_group_id(test_id);
  auto const group_name = this->get_group_name(group_id);

  this->report_error(
    ErrorType::Init_TestHasNoBody,
    std::format(
      R"(Test "{}" in group "{}" is incomplete. )"
      R"(Call the run(...) method to fix this.)",
      test_name,
      group_name));
}

auto TestRun_impl::get_passing_assertions(TestId const test_id) const
  -> std::vector<AssertionRecord>
{
  if(this->passing_assertions_.contains(test_id))
  {
    return this->passing_assertions_.at(test_id);
  }

  return {};
}

auto TestRun_impl::get_failing_assertions(TestId const test_id) const
  -> std::vector<AssertionRecord>
{
  if(this->failing_assertions_.contains(test_id))
  {
    return this->failing_assertions_.at(test_id);
  }

  return {};
}

auto TestRun_impl::has_failing_assertions() const -> bool
{
  return !this->failing_assertions_.empty();
}

auto TestRun_impl::make_in_process_context(TestId const test_id) const
  -> std::unique_ptr<Context>
{
  auto *impl = new ContextInProcess_impl{};

  impl->initialize(*this->test_run_, test_id);

  // NOLINTNEXTLINE(clang-analyzer-cplusplus.NewDeleteLeaks)
  return std::unique_ptr<ContextInProcess>(new ContextInProcess{impl});
}

auto TestRun_impl::make_child_process_context(
  TestId const test_id,
  InputPipeEnd const &response_write_pipe,
  std::mutex &transmission_mutex) const -> std::unique_ptr<Context>
{
  auto *impl = new ContextChildProcess_impl{};

  impl->initialize(
    *this->test_run_,
    test_id,
    response_write_pipe,
    transmission_mutex);

  // NOLINTNEXTLINE(clang-analyzer-cplusplus.NewDeleteLeaks)
  return std::unique_ptr<ContextChildProcess>(new ContextChildProcess{impl});
}

namespace
{

auto discard_until_within_range(auto &rng, std::uint64_t const max)
  -> std::uint64_t
{
  std::uint64_t next_value = 0;
  // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_START
  while((next_value = rng()) > max)
  {
  }
  // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_STOP

  return next_value;
}

class TruncatedRng
{
public:
  constexpr static std::uint64_t TRUNCATED_RNG_MAX = 0xffff'ffff'ffff'fffeU;

  TruncatedRng()
    : rng_{0x0123'4567'89ab'cdefU}
  {
    this->rng_.discard(0x1234U);
  }

  auto operator()() -> std::uint64_t
  {
    return discard_until_within_range(this->rng_, TRUNCATED_RNG_MAX);
  }

private:
  using knuth_lcg = std::linear_congruential_engine<
    std::uint64_t,
    6'364'136'223'846'793'005U,
    1'442'695'040'888'963'407U,
    0U>;

  knuth_lcg rng_;
};

auto get_random_number_generator() noexcept -> TruncatedRng
{
  return TruncatedRng{};
}

auto get_test_record_ptrs(TestRun const &t) noexcept
  -> std::vector<TestRecord *>
{
  auto &test_records = get_impl(t).test_records();
  std::vector<TestRecord *> ptrs;
  ptrs.reserve(test_records.size());

  std::ranges::transform(
    test_records,
    std::back_inserter(ptrs),
    [](auto &test_record)
    {
      return &test_record;
    });

  return ptrs;
}

// Unsophisticated, but works well enough for our purposes
auto uniform_number(TruncatedRng &rng, std::uint64_t const max) -> std::uint64_t
{
  auto const cycle_length = max + 1;

  auto const rng_max_full_cycles =
    ((TruncatedRng::TRUNCATED_RNG_MAX + 1) / cycle_length * cycle_length) - 1;

  return discard_until_within_range(rng, rng_max_full_cycles) % cycle_length;
}

void Fisher_Yates_shuffle(std::vector<TestRecord *> &vec, TruncatedRng &rng)
{
  if(vec.empty())
  {
    return;
  }

  for(std::uint64_t i = vec.size() - 1; i > 0; --i)
  {
    using std::swap;
    swap(vec[i], vec[uniform_number(rng, i)]);
  }
}

auto get_shuffled_test_record_ptrs_(TestRun const &t) noexcept
  -> std::vector<TestRecord *>
{
  auto ptrs = get_test_record_ptrs(t);

  auto rng = get_random_number_generator();

  Fisher_Yates_shuffle(ptrs, rng);

  return ptrs;
}

} // namespace

void TestRun_impl::set_shuffled_test_record_ptrs()
{
  this->shuffled_test_record_ptrs_ =
    get_shuffled_test_record_ptrs_(*this->test_run_);
}

auto TestRun_impl::get_shuffled_test_record_ptrs() const
  -> std::vector<TestRecord *> const &
{
  return this->shuffled_test_record_ptrs_;
}

auto TestRun_impl::is_disabled(TestId const test_id) const -> bool
{
  auto const &record = this->test_records_[test_id];

  return record.disabled();
}

void TestRun_impl::register_crashed_exit_status(
  TestId const crashed_test_id,
  unsigned long long const exit_status)
{
  crashed_exit_statuses_[crashed_test_id] = exit_status;
}

auto TestRun_impl::get_crashed_exit_status(TestId const test_id) const
  -> std::optional<unsigned long long>
{
  if(this->crashed_exit_statuses_.contains(test_id))
  {
    return {this->crashed_exit_statuses_.at(test_id)};
  }

  return std::nullopt;
}

auto TestRun_impl::errors() const noexcept -> std::vector<std::string>
{
  return std::ranges::views::transform(
           this->errors_,
           [](Error const &error)
           {
             return error.message;
           }) |
    std::ranges::to<std::vector<std::string>>();
}

auto TestRun_impl::has_errors() const -> bool
{
  return !this->errors_.empty();
}

void TestRun_impl::initialize(TestRun const &test_run)
{
  this->test_run_ = &test_run;
}

void TestRun_impl::register_test_assembly(
  TestAssembly assembly,
  TestId const test_id,
  unsigned long long const timeout_ms,
  bool const disabled)
{
  this->test_records_
    .emplace_back(std::move(assembly), test_id, timeout_ms, disabled);
}

auto TestRun_impl::test_records() -> std::vector<TestRecord> &
{
  return this->test_records_;
}

auto TestRun_impl::generate_results() const -> TestRunResult
{
  auto *impl = new TestRunResult_impl{};

  impl->initialize(*this->test_run_);

  return TestRunResult{impl};
}

void TestRun_impl::register_assertion(
  bool const condition,
  TestId const test_id,
  AssertionIndex const index,
  std::optional<std::string> maybe_message)
{
  if(condition)
  {
    this->passing_assertions_[test_id].emplace_back(
      condition,
      index,
      std::move(maybe_message));
  }
  else
  {
    this->failing_assertions_[test_id].emplace_back(
      condition,
      index,
      std::move(maybe_message));
  }
}

void TestRun_impl::transmit_assertion(
  bool const condition,
  TestId const test_id,
  AssertionIndex const index,
  std::optional<std::string> const &maybe_message,
  InputPipeEnd const &response_write_pipe) const
{
  constexpr auto code = std::to_underlying(Response::Code::Assertion);
  response_write_pipe.write(&code, sizeof code);

  unsigned long long const test_id_ = test_id;
  response_write_pipe.write(
    reinterpret_cast<unsigned char const *>(&test_id_),
    sizeof test_id_);

  unsigned char const passed = condition ? 1 : 0;
  response_write_pipe.write(&passed, sizeof passed);

  unsigned long long const index_ = index;
  response_write_pipe.write(
    reinterpret_cast<unsigned char const *>(&index_),
    sizeof index_);

  if(maybe_message.has_value())
  {
    constexpr unsigned char has_message = 1;
    response_write_pipe.write(&has_message, sizeof has_message);

    auto const &message = maybe_message.value();
    unsigned long long const message_size = message.size();
    response_write_pipe.write(
      reinterpret_cast<unsigned char const *>(&message_size),
      sizeof message_size);
    response_write_pipe.write(
      reinterpret_cast<unsigned char const *>(message.data()),
      message_size);
  }
  else
  {
    constexpr unsigned char has_message = 0;
    response_write_pipe.write(&has_message, sizeof has_message);
  }
}

TestRunResult_impl::TestRunResult_impl()
  : has_failing_assertions_{false}
{
}

void TestRunResult_impl::initialize(TestRun const &test_run)
{
  this->errors_ = std::invoke(
    [&test_run]()
    {
      return get_impl(test_run).errors();
    });

  if(!this->errors_.empty())
  {
    return;
  }

  this->has_failing_assertions_ = get_impl(test_run).has_failing_assertions();

  this->test_outcomes_ = std::invoke(
    [&test_run]()
    {
      unsigned long long const n = get_impl(test_run).test_count();

      std::vector<std::unique_ptr<TestOutcome>> output;
      output.reserve(n);

      for(unsigned long long id = 0; id < n; ++id)
      {
        output.emplace_back(get_impl(test_run).make_test_outcome(id));
      }

      return output;
    });
}

auto TestRunResult_impl::errors() const -> std::vector<std::string> const &
{
  return this->errors_;
}

auto TestRunResult_impl::has_errors() const -> bool
{
  return !this->errors_.empty();
}

auto TestRunResult_impl::has_failing_assertions() const -> bool
{
  return this->has_failing_assertions_;
}

auto TestRunResult_impl::has_crashes() const -> bool
{
  auto const it = std::ranges::find_if(
    this->test_outcomes_,
    [](auto const &outcome)
    {
      return outcome->status() == TestOutcome::Status::Terminated;
    });

  return it != this->test_outcomes_.end();
}

auto TestRunResult_impl::has_timeouts() const -> bool
{
  auto const it = std::ranges::find_if(
    this->test_outcomes_,
    [](auto const &outcome)
    {
      return outcome->status() == TestOutcome::Status::Timeout;
    });

  return it != this->test_outcomes_.end();
}

auto TestRunResult_impl::test_outcome_count() const -> unsigned long long
{
  return this->test_outcomes_.size();
}

auto TestRunResult_impl::get_test_outcome(unsigned long long const index) const
  -> TestOutcome const &
{
  return *this->test_outcomes_[index];
}

AutorunFunctionPtrVector_impl::~AutorunFunctionPtrVector_impl() = default;

AutorunFunctionPtrVector_impl::AutorunFunctionPtrVector_impl() noexcept =
  default;

auto AutorunFunctionPtrVector_impl::get_data() noexcept
  -> std::vector<AutorunFunctionPtr> &
{
  return this->data_;
}

} // namespace waypoint::internal
