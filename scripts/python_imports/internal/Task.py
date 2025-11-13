# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

import time
import typing

from .time_utils import ns_to_string


class Task:
    def __init__(self, name: str, fn: typing.Callable[[], bool] | None = None):
        assert name is not None
        self.name_ = name
        self.fn_ = fn
        self.task_attempted_ = False
        self.deps_success_ = False
        self.success_ = False
        self.dependencies_ = []

    def depends_on(self, deps: typing.List["Task"]):
        for d in deps:
            self.dependencies_.append(d)

    def run(self) -> bool:
        if self.task_attempted_ and not (self.deps_success_ and self.success_):
            return False

        if self.task_attempted_ and self.deps_success_ and self.success_:
            return True

        self.task_attempted_ = True

        start_deps = time.time_ns()

        if len(self.dependencies_) > 0:
            print(f"Preparing task: {self.name_}")
        for d in self.dependencies_:
            success = d.run()
            if not success:
                return False

        self.deps_success_ = True

        print(f"Running task: {self.name_}")
        start = time.time_ns()
        success = True if self.fn_ is None else self.fn_()
        if len(self.dependencies_) > 0:
            print(
                "Finished task:",
                f"{self.name_} ({ns_to_string(time.time_ns() - start)},",
                f"total: {ns_to_string(time.time_ns() - start_deps)})",
            )
        else:
            print(
                "Finished task:",
                f"{self.name_} ({ns_to_string(time.time_ns() - start)})",
            )
        if not success:
            if len(self.dependencies_) > 0:
                print(
                    "Task failed:",
                    f"{self.name_} ({ns_to_string(time.time_ns() - start)},",
                    f"total: {ns_to_string(time.time_ns() - start_deps)})",
                )
            else:
                print(
                    "Task failed:",
                    f"{self.name_} ({ns_to_string(time.time_ns() - start)})",
                )

            return False

        self.success_ = True

        return True
