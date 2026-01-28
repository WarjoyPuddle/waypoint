// Copyright (c) 2025-2026 Wojciech Kałuża
// SPDX-License-Identifier: MIT
// For license details, see LICENSE file

#include "waypoint.hpp"

#include "impls.hpp"
#include "types.hpp"

#include "coverage/coverage.hpp"
#include "process/process.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <functional>
#include <latch>
#include <mutex>
#include <optional>
#include <span>
#include <string>
#include <thread>
#include <tuple>
#include <utility>
#include <vector>

namespace waypoint::internal
{

auto get_autorun_tests() noexcept -> AutorunManagerTests &
{
  // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_START
  static AutorunManagerTests tests{new AutorunFunctionPtrVector_impl{}};
  // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_STOP

  return tests;
}

auto add_autorun_test(AutorunFunctionPtr const fn) noexcept -> int
{
  get_autorun_tests().push_back(fn);

  return 0;
}

AutorunFunctionPtrVector::~AutorunFunctionPtrVector() = default;

AutorunFunctionPtrVector::AutorunFunctionPtrVector(
  AutorunFunctionPtrVector_impl *const impl) noexcept
  : impl_{UniquePtr{impl}}
{
}

auto AutorunFunctionPtrVector::operator[](
  unsigned long long const i) const noexcept -> AutorunFunctionPtr
{
  return this->impl_->get_data()[i];
}

void AutorunFunctionPtrVector::push_back(
  AutorunFunctionPtr const ptr) const noexcept
{
  this->impl_->get_data().push_back(ptr);
}

auto AutorunFunctionPtrVector::size() const noexcept -> unsigned long long
{
  return this->impl_->get_data().size();
}

auto get_impl(TestRun const &test_run) -> TestRun_impl &
{
  return *test_run.impl_;
}

} // namespace waypoint::internal

namespace
{

void send_timeout(
  waypoint::internal::InputPipeEnd const &response_write_pipe,
  waypoint::TestId const test_id)
{
  constexpr auto code =
    std::to_underlying(waypoint::internal::Response::Code::Timeout);
  response_write_pipe.write(&code, sizeof code);

  unsigned long long const test_id_ = test_id;
  response_write_pipe.write(
    reinterpret_cast<unsigned char const *>(&test_id_),
    sizeof test_id_);
}

class Timeout
{
public:
  ~Timeout()
  {
    this->thread_.join();
  }

  Timeout(Timeout const &other) = delete;
  Timeout(Timeout &&other) noexcept = delete;
  auto operator=(Timeout const &other) -> Timeout & = delete;
  auto operator=(Timeout &&other) noexcept -> Timeout & = delete;

  explicit Timeout(
    waypoint::TestId const test_id,
    unsigned long long const timeout_ms,
    std::mutex &transmission_mutex,
    waypoint::internal::InputPipeEnd const &response_write_pipe)
    : transmission_mutex_{transmission_mutex},
      response_write_pipe_{response_write_pipe},
      test_id_{test_id},
      timeout_ms_{timeout_ms},
      latch_{2},
      is_armed_{true},
      thread_{[this]()
              {
                this->latch_arrive_and_wait();

                std::unique_lock lock{this->transmission_mutex_};

                bool const disarmed = this->cv_.wait_for(
                  lock,
                  std::chrono::milliseconds{this->timeout_ms_},
                  [this]()
                  {
                    return !this->is_armed_.load();
                  });

                if(disarmed)
                {
                  return;
                }

                send_timeout(this->response_write_pipe_, this->test_id_);

                waypoint::coverage::gcov_dump();

                // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_START
                std::abort();
                // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_STOP
              }}
  {
    this->latch_arrive_and_wait();
  }

  void disarm()
  {
    std::lock_guard const lock{this->transmission_mutex_};

    this->is_armed_.store(false);
    this->cv_.notify_one();
  }

private:
  void latch_arrive_and_wait()
  {
    // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_START
    this->latch_.arrive_and_wait();
    // GCOV_COVERAGE_58QuSuUgMN8onvKx_EXCL_BR_STOP
  }

  std::mutex &transmission_mutex_;
  waypoint::internal::InputPipeEnd const &response_write_pipe_;
  unsigned long long test_id_;
  unsigned long long timeout_ms_;
  std::latch latch_;
  std::condition_variable cv_;
  std::atomic<bool> is_armed_;
  std::thread thread_;
};

void populate_test_indices_(waypoint::TestRun const &t)
{
  waypoint::internal::get_impl(t).set_shuffled_test_record_ptrs();
  auto const &shuffled_ptrs =
    waypoint::internal::get_impl(t).get_shuffled_test_record_ptrs();
  for(unsigned long long i = 0; i < shuffled_ptrs.size(); ++i)
  {
    waypoint::internal::get_impl(t).set_test_index(
      shuffled_ptrs[i]->test_id(),
      i);
  }
}

void run_test(
  waypoint::TestRun const &t,
  unsigned long long const test_index,
  waypoint::internal::InputPipeEnd const &response_write_pipe,
  std::mutex &transmission_mutex) noexcept
{
  auto const &impl = waypoint::internal::get_impl(t);
  waypoint::internal::TestRecord *const record =
    impl.get_shuffled_test_record_ptrs().at(test_index);

  auto const test_id = record->test_id();

  auto const ctx = impl.make_child_process_context(
    test_id,
    response_write_pipe,
    transmission_mutex);

  auto const timeout_ms = record->timeout_ms();
  if(timeout_ms == 0)
  {
    record->test_assembly()(*ctx);
  }
  else
  {
    Timeout timeout{
      test_id,
      timeout_ms,
      transmission_mutex,
      response_write_pipe};
    record->test_assembly()(*ctx);
    timeout.disarm();
  }
  record->mark_as_run();
}

void execute_command(
  waypoint::TestRun const &t,
  waypoint::internal::Command const &command,
  waypoint::internal::InputPipeEnd const &response_write_pipe,
  std::mutex &transmission_mutex)
{
  if(command.code == waypoint::internal::Command::Code::RunTest)
  {
    run_test(t, command.test_index, response_write_pipe, transmission_mutex);
  }
}

void begin_handshake(waypoint::internal::InputPipeEnd const &pipe)
{
  constexpr auto cmd =
    std::to_underlying(waypoint::internal::Command::Code::Attention);

  pipe.write(&cmd, sizeof cmd);
}

void await_handshake_start(
  waypoint::internal::OutputPipeEnd const &pipe,
  std::mutex &transmission_mutex)
{
  std::lock_guard const lock{transmission_mutex};

  unsigned char data = 0;
  [[maybe_unused]]
  auto const read_result = pipe.read_exactly(&data, sizeof data);
}

void complete_handshake(
  waypoint::internal::InputPipeEnd const &pipe,
  std::mutex &transmission_mutex)
{
  std::lock_guard const lock{transmission_mutex};

  constexpr auto ready =
    std::to_underlying(waypoint::internal::Response::Code::Ready);

  pipe.write(&ready, sizeof ready);
}

void await_handshake_end(waypoint::internal::OutputPipeEnd const &pipe)
{
  unsigned char data = 0;
  [[maybe_unused]]
  auto const read_result = pipe.read_exactly(&data, sizeof data);
}

auto receive_command(
  waypoint::internal::OutputPipeEnd const &command_read_pipe,
  std::mutex &transmission_mutex) -> waypoint::internal::Command
{
  std::lock_guard const lock{transmission_mutex};

  auto code_ = std::to_underlying(waypoint::internal::Command::Code::Invalid);
  [[maybe_unused]]
  auto read_result = command_read_pipe.read_exactly(&code_, sizeof code_);

  auto const code = static_cast<waypoint::internal::Command::Code>(code_);

  if(code == waypoint::internal::Command::Code::RunTest)
  {
    unsigned long long test_index = 0;
    read_result = command_read_pipe.read_exactly(
      reinterpret_cast<unsigned char *>(&test_index),
      sizeof test_index);

    return {code, test_index};
  }

  return {code, {}};
}

auto receive_response(
  waypoint::internal::OutputPipeEnd const &response_read_pipe)
  -> std::optional<waypoint::internal::Response>
{
  auto code_ = std::to_underlying(waypoint::internal::Response::Code::Invalid);
  [[maybe_unused]]
  auto read_result = response_read_pipe.read_exactly(&code_, sizeof code_);
  if(read_result == waypoint::internal::OutputPipeEnd::ReadResult::PipeClosed)
  {
    return std::nullopt;
  }

  auto const code = static_cast<waypoint::internal::Response::Code>(code_);

  if(
    code != waypoint::internal::Response::Code::Assertion &&
    code != waypoint::internal::Response::Code::TestComplete &&
    code != waypoint::internal::Response::Code::Timeout)
  {
    return {waypoint::internal::Response{code, {}, {}, {}, {}}};
  }

  unsigned long long test_id = 0;
  read_result = response_read_pipe.read_exactly(
    reinterpret_cast<unsigned char *>(&test_id),
    sizeof test_id);

  if(
    code == waypoint::internal::Response::Code::TestComplete ||
    code == waypoint::internal::Response::Code::Timeout)
  {
    return {waypoint::internal::Response{code, test_id, {}, {}, {}}};
  }

  unsigned char passed = 0;
  read_result = response_read_pipe.read_exactly(&passed, sizeof passed);

  unsigned long long assertion_index = 0;
  read_result = response_read_pipe.read_exactly(
    reinterpret_cast<unsigned char *>(&assertion_index),
    sizeof assertion_index);

  unsigned char has_message = 0;
  read_result =
    response_read_pipe.read_exactly(&has_message, sizeof has_message);
  if(has_message == 0)
  {
    return {waypoint::internal::Response{
      code,
      test_id,
      passed == 1,
      assertion_index,
      std::nullopt}};
  }

  unsigned long long message_size = 0;
  read_result = response_read_pipe.read_exactly(
    reinterpret_cast<unsigned char *>(&message_size),
    sizeof message_size);

  std::string message(message_size, 'X');
  read_result = response_read_pipe.read_exactly(
    reinterpret_cast<unsigned char *>(message.data()),
    message_size);

  return {waypoint::internal::Response{
    code,
    test_id,
    passed == 1,
    assertion_index,
    {message}}};
}

void send_command(
  waypoint::internal::InputPipeEnd const &command_write_pipe,
  waypoint::internal::Command const &command)
{
  auto const code = std::to_underlying(command.code);
  command_write_pipe.write(&code, sizeof code);
  if(command.code == waypoint::internal::Command::Code::RunTest)
  {
    auto const test_index = command.test_index;
    command_write_pipe.write(
      reinterpret_cast<unsigned char const *>(&test_index),
      sizeof test_index);
  }
}

void send_response(
  waypoint::TestRun const &t,
  waypoint::internal::InputPipeEnd const &response_write_pipe,
  unsigned long long const test_index,
  waypoint::internal::Response::Code const &code_,
  std::mutex &transmission_mutex)
{
  std::lock_guard const lock{transmission_mutex};

  auto const code = std::to_underlying(code_);
  response_write_pipe.write(&code, sizeof code);
  if(code_ == waypoint::internal::Response::Code::TestComplete)
  {
    waypoint::internal::TestRecord const *const record =
      waypoint::internal::get_impl(t).get_shuffled_test_record_ptrs().at(
        test_index);
    auto const test_id = record->test_id();
    response_write_pipe.write(
      reinterpret_cast<unsigned char const *>(&test_id),
      sizeof test_id);
  }
}

auto is_end_command(waypoint::internal::Command const &command) -> bool
{
  return command.code == waypoint::internal::Command::Code::End;
}

void shut_down_sequence(
  waypoint::internal::InputPipeEnd const &command_write_pipe,
  waypoint::internal::OutputPipeEnd const &response_read_pipe) noexcept
{
  constexpr auto command =
    waypoint::internal::Command{waypoint::internal::Command::Code::End, {}};

  send_command(command_write_pipe, command);

  [[maybe_unused]]
  auto const maybe_response = receive_response(response_read_pipe);
}

auto parent_main(
  waypoint::TestRun const &t,
  waypoint::internal::InputPipeEnd const &command_write_pipe,
  waypoint::internal::OutputPipeEnd const &response_read_pipe,
  unsigned long long const initial_test_index) noexcept
  -> std::tuple<waypoint::TestRunResult, bool, unsigned long long>
{
  begin_handshake(command_write_pipe);
  await_handshake_end(response_read_pipe);

  auto &impl = waypoint::internal::get_impl(t);

  auto const &all_records = impl.get_shuffled_test_record_ptrs();
  auto const record_subset = std::span(
    all_records.data() + initial_test_index,
    all_records.size() - initial_test_index);

  for(auto *record : record_subset)
  {
    if(record->disabled())
    {
      continue;
    }

    auto const test_index = impl.get_test_index(record->test_id());

    auto const command = waypoint::internal::Command{
      waypoint::internal::Command::Code::RunTest,
      test_index};
    send_command(command_write_pipe, command);

    while(true)
    {
      auto const maybe_response = receive_response(response_read_pipe);
      if(!maybe_response.has_value())
      {
        record->mark_as_crashed();

        return {
          impl.generate_results(),
          true,
          impl.get_test_index(record->test_id())};
      }

      auto const &response = maybe_response.value();
      if(response.code == waypoint::internal::Response::Code::Assertion)
      {
        impl.register_assertion(
          response.assertion_passed,
          response.test_id,
          response.assertion_index,
          response.assertion_message);
      }

      if(response.code == waypoint::internal::Response::Code::Timeout)
      {
        record->mark_as_timed_out();

        return {
          impl.generate_results(),
          true,
          impl.get_test_index(record->test_id())};
      }

      if(response.code == waypoint::internal::Response::Code::TestComplete)
      {
        record->mark_as_run();
        break;
      }
    }
  }

  shut_down_sequence(command_write_pipe, response_read_pipe);

  return {impl.generate_results(), false, 0};
}

void child_main(
  waypoint::TestRun const &t,
  waypoint::internal::OutputPipeEnd const &command_read_pipe,
  waypoint::internal::InputPipeEnd const &response_write_pipe) noexcept
{
  std::mutex transmission_mutex;

  await_handshake_start(command_read_pipe, transmission_mutex);
  complete_handshake(response_write_pipe, transmission_mutex);

  while(true)
  {
    auto const command = receive_command(command_read_pipe, transmission_mutex);

    execute_command(t, command, response_write_pipe, transmission_mutex);
    send_response(
      t,
      response_write_pipe,
      command.test_index,
      std::invoke(
        [&command]()
        {
          if(command.code == waypoint::internal::Command::Code::RunTest)
          {
            return waypoint::internal::Response::Code::TestComplete;
          }

          return waypoint::internal::Response::Code::ShuttingDown;
        }),
      transmission_mutex);

    if(is_end_command(command))
    {
      break;
    }
  }
}

void initialize(waypoint::TestRun const &t) noexcept
{
  auto const &functions = waypoint::internal::get_autorun_tests();
  for(unsigned long long i = 0; i < functions.size(); ++i)
  {
    auto const fn_ptr = functions[i];
    fn_ptr(t);
  }

  populate_test_indices_(t);
}

} // namespace

namespace waypoint
{

auto run_all_tests_in_process(TestRun const &t) noexcept -> TestRunResult
{
  initialize(t);
  if(internal::get_impl(t).has_errors())
  {
    // Initialization had errors, skip running tests and emit results
    return internal::get_impl(t).generate_results();
  }

  std::ranges::for_each(
    internal::get_impl(t).get_shuffled_test_record_ptrs(),
    [&t](auto *const ptr) noexcept
    {
      if(!ptr->disabled())
      {
        auto const context =
          internal::get_impl(t).make_in_process_context(ptr->test_id());

        // Run test
        ptr->test_assembly()(*context);
        ptr->mark_as_run();
      }
    });

  return internal::get_impl(t).generate_results();
}

auto run_all_tests(TestRun const &t) noexcept -> TestRunResult
{
  initialize(t);
  auto &impl = internal::get_impl(t);
  if(impl.has_errors())
  {
    // Initialization had errors, skip running tests and emit results
    return impl.generate_results();
  }

  if(waypoint::internal::is_child())
  {
    {
      auto const pipes = waypoint::internal::get_pipes_from_env();

      auto const &command_read_pipe = pipes.first;
      auto const &response_write_pipe = pipes.second;

      child_main(t, command_read_pipe, response_write_pipe);
    }

    std::exit(0);
  }

  unsigned long long initial_test_index = 0;
  while(true)
  {
    waypoint::internal::ChildProcess const child;

    auto results = parent_main(
      t,
      child.command_write_pipe(),
      child.response_read_pipe(),
      initial_test_index);
    auto run_result = std::move(std::get<0>(results));
    auto const crash_or_timeout = std::get<1>(results);
    auto const creshed_test_index = std::get<2>(results);

    auto const exit_status = child.wait();

    if(!crash_or_timeout)
    {
      return run_result;
    }

    auto const *record =
      impl.get_shuffled_test_record_ptrs().at(creshed_test_index);
    if(record->status() == internal::TestRecord::Status::Terminated)
    {
      auto const crashed_test_id = record->test_id();
      impl.register_crashed_exit_status(crashed_test_id, exit_status);
    }

    initial_test_index = creshed_test_index + 1;
  }

  std::unreachable();
}

AssertionOutcome::~AssertionOutcome() = default;

AssertionOutcome::AssertionOutcome(internal::AssertionOutcome_impl *const impl)
  : impl_{internal::UniquePtr{impl}}
{
}

auto AssertionOutcome::group() const noexcept -> char const *
{
  return this->impl_->group_name();
}

auto AssertionOutcome::test() const noexcept -> char const *
{
  return this->impl_->test_name();
}

auto AssertionOutcome::message() const noexcept -> char const *
{
  if(this->impl_->message().has_value())
  {
    return this->impl_->message().value().c_str();
  }

  return nullptr;
}

auto AssertionOutcome::passed() const noexcept -> bool
{
  return this->impl_->passed();
}

auto AssertionOutcome::index() const noexcept -> unsigned long long
{
  return this->impl_->index();
}

TestOutcome::~TestOutcome() = default;

TestOutcome::TestOutcome(internal::TestOutcome_impl *const impl)
  : impl_{internal::UniquePtr{impl}}
{
}

auto TestOutcome::group_name() const noexcept -> char const *
{
  return this->impl_->get_group_name().c_str();
}

auto TestOutcome::test_name() const noexcept -> char const *
{
  return this->impl_->get_test_name().c_str();
}

auto TestOutcome::test_index() const noexcept -> unsigned long long
{
  return this->impl_->get_index();
}

auto TestOutcome::assertion_count() const noexcept -> unsigned long long
{
  return this->impl_->get_assertion_count();
}

auto TestOutcome::assertion_outcome(
  unsigned long long const index) const noexcept -> AssertionOutcome const &
{
  return this->impl_->get_assertion_outcome(index);
}

auto TestOutcome::disabled() const noexcept -> bool
{
  return this->impl_->disabled();
}

auto TestOutcome::status() const noexcept -> TestOutcome::Status
{
  return this->impl_->status();
}

auto TestOutcome::exit_code() const noexcept -> unsigned long long const *
{
  auto const &maybe_exit_code = this->impl_->exit_status();
  if(maybe_exit_code.has_value())
  {
    auto const &exit_code = maybe_exit_code.value();

    return &exit_code;
  }

  return nullptr;
}

Group::~Group() = default;

Group::Group(internal::Group_impl *const impl)
  : impl_{impl}
{
}

Test3<void>::~Test3() = default;

Test3<void>::Test3(internal::Registrar<void> registrar)
  : registrar_{internal::move(registrar)}
{
}

void Test3<void>::disable() && noexcept
{
  this->registrar_.disable(true);
}

void Test3<void>::disable(bool const is_disabled) && noexcept
{
  this->registrar_.disable(is_disabled);
}

Test2<void>::~Test2() = default;

Test2<void>::Test2(internal::Registrar<void> registrar)
  : registrar_{internal::move(registrar)}
{
}

Test::~Test() = default;

Test::Test(internal::Test_impl *const impl)
  : impl_{internal::UniquePtr{impl}}
{
}

auto Test::test_id() const -> unsigned long long
{
  return this->impl_->get_id();
}

auto Test::get_test_run() const -> TestRun const &
{
  return this->impl_->get_test_run();
}

void Test::mark_complete() const
{
  this->impl_->mark_complete();
}

auto TestRun::group(char const *name) const noexcept -> Group
{
  auto const group_id = this->impl_->register_group(name);

  return this->impl_->make_group(group_id);
}

auto TestRun::test(Group const &group, char const *const name) const noexcept
  -> Test
{
  auto const test_id =
    this->impl_->register_test(this->impl_->get_group_id(group), name);

  return this->impl_->make_test(test_id);
}

auto TestRun::create() -> TestRun
{
  auto *impl = new internal::TestRun_impl{};

  return TestRun{impl};
}

void TestRun::register_test_assembly(
  internal::TestAssembly f,
  unsigned long long const test_id,
  unsigned long long const timeout_ms,
  bool const disabled) const
{
  this->impl_
    ->register_test_assembly(std::move(f), test_id, timeout_ms, disabled);
}

void TestRun::report_incomplete_test(unsigned long long const test_id) const
{
  this->impl_->report_incomplete_test(test_id);
}

TestRun::~TestRun() = default;

TestRun::TestRun(internal::TestRun_impl *const impl)
  : impl_{internal::UniquePtr{impl}}
{
  impl->initialize(*this);
}

Context::~Context() = default;

Context::Context() = default;

ContextInProcess::~ContextInProcess() = default;

ContextInProcess::ContextInProcess(internal::ContextInProcess_impl *const impl)
  : impl_{internal::UniquePtr{impl}}
{
}

void ContextInProcess::assert(bool const condition) const noexcept
{
  internal::get_impl(impl_->get_test_run())
    .register_assertion(
      condition,
      this->impl_->test_id(),
      this->impl_->generate_assertion_index(),
      std::nullopt);
}

void ContextInProcess::assert(bool const condition, char const *const message)
  const noexcept
{
  internal::get_impl(impl_->get_test_run())
    .register_assertion(
      condition,
      this->impl_->test_id(),
      this->impl_->generate_assertion_index(),
      message);
}

auto ContextInProcess::assume(bool const condition) const noexcept -> bool
{
  internal::get_impl(impl_->get_test_run())
    .register_assertion(
      condition,
      this->impl_->test_id(),
      this->impl_->generate_assertion_index(),
      std::nullopt);

  return condition;
}

auto ContextInProcess::assume(bool const condition, char const *const message)
  const noexcept -> bool
{
  internal::get_impl(impl_->get_test_run())
    .register_assertion(
      condition,
      this->impl_->test_id(),
      this->impl_->generate_assertion_index(),
      message);

  return condition;
}

ContextChildProcess::~ContextChildProcess() = default;

ContextChildProcess::ContextChildProcess(
  internal::ContextChildProcess_impl *const impl)
  : impl_{internal::UniquePtr{impl}}
{
}

void ContextChildProcess::assert(bool const condition) const noexcept
{
  std::lock_guard const lock{*this->impl_->transmission_mutex()};

  auto const index = this->impl_->generate_assertion_index();

  internal::get_impl(impl_->get_test_run())
    .register_assertion(condition, this->impl_->test_id(), index, std::nullopt);

  internal::get_impl(impl_->get_test_run())
    .transmit_assertion(
      condition,
      this->impl_->test_id(),
      index,
      std::nullopt,
      *this->impl_->response_write_pipe());
}

void ContextChildProcess::assert(
  bool const condition,
  char const *const message) const noexcept
{
  std::lock_guard const lock{*this->impl_->transmission_mutex()};

  auto const index = this->impl_->generate_assertion_index();

  internal::get_impl(impl_->get_test_run())
    .register_assertion(condition, this->impl_->test_id(), index, message);

  internal::get_impl(impl_->get_test_run())
    .transmit_assertion(
      condition,
      this->impl_->test_id(),
      index,
      message,
      *this->impl_->response_write_pipe());
}

auto ContextChildProcess::assume(bool const condition) const noexcept -> bool
{
  std::lock_guard const lock{*this->impl_->transmission_mutex()};

  auto const index = this->impl_->generate_assertion_index();

  internal::get_impl(impl_->get_test_run())
    .register_assertion(condition, this->impl_->test_id(), index, std::nullopt);

  internal::get_impl(impl_->get_test_run())
    .transmit_assertion(
      condition,
      this->impl_->test_id(),
      index,
      std::nullopt,
      *this->impl_->response_write_pipe());

  return condition;
}

auto ContextChildProcess::assume(
  bool const condition,
  char const *const message) const noexcept -> bool
{
  std::lock_guard const lock{*this->impl_->transmission_mutex()};

  auto const index = this->impl_->generate_assertion_index();

  internal::get_impl(impl_->get_test_run())
    .register_assertion(condition, this->impl_->test_id(), index, message);

  internal::get_impl(impl_->get_test_run())
    .transmit_assertion(
      condition,
      this->impl_->test_id(),
      index,
      message,
      *this->impl_->response_write_pipe());

  return condition;
}

TestRunResult::~TestRunResult() = default;

TestRunResult::TestRunResult(TestRunResult &&other) noexcept = default;

TestRunResult::TestRunResult(internal::TestRunResult_impl *const impl)
  : impl_{internal::MoveableUniquePtr<internal::TestRunResult_impl>{impl}}
{
}

auto TestRunResult::success() const noexcept -> bool
{
  return !this->impl_->has_errors() &&
    !this->impl_->has_failing_assertions() &&
    !this->impl_->has_crashes() &&
    !this->impl_->has_timeouts();
}

auto TestRunResult::test_count() const noexcept -> unsigned long long
{
  return this->impl_->test_outcome_count();
}

auto TestRunResult::test_outcome(unsigned long long const index) const noexcept
  -> TestOutcome const &
{
  return this->impl_->get_test_outcome(index);
}

auto TestRunResult::error_count() const noexcept -> unsigned long long
{
  return this->impl_->errors().size();
}

auto TestRunResult::error(unsigned long long const index) const noexcept
  -> char const *
{
  return this->impl_->errors().at(index).c_str();
}

} // namespace waypoint
