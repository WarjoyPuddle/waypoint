# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file


def ns_to_string(nanos) -> str:
    one_second_ns = 10**9
    one_minute_ns = 60 * one_second_ns
    one_hour_ns = 60 * one_minute_ns
    one_day_ns = 24 * one_hour_ns

    if nanos > one_day_ns:
        days = int(nanos / one_day_ns)
        hours = int((nanos % one_day_ns) / one_hour_ns)
        minutes = int((nanos % one_hour_ns) / one_minute_ns)

        return f"{days}d {hours}h {minutes}m"
    if nanos > one_hour_ns:
        hours = int(nanos / one_hour_ns)
        minutes = int((nanos % one_hour_ns) / one_minute_ns)
        seconds = int((nanos % one_minute_ns) / one_second_ns)

        return f"{hours}h {minutes}m {seconds}s"
    if nanos > one_minute_ns:
        minutes = int(nanos / one_minute_ns)
        seconds = int((nanos % one_minute_ns) / one_second_ns)

        return f"{minutes}m {seconds}s"
    if nanos > one_second_ns:
        return f"{round(nanos / one_second_ns, 1)}s"
    if nanos > 10**6:
        return f"{round(nanos / 10 ** 6, 1)}ms"
    if nanos > 10**3:
        return f"{round(nanos / 10 ** 3, 1)}us"

    return f"{nanos}ns"
