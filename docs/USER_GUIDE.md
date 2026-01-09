# User Guide

## Contents

1. [Anatomy of a Waypoint test](#anatomy-of-a-waypoint-test)

## Anatomy of a Waypoint test

In the simplest case, a Waypoint test consists of a body supplied as a
callable to the `run()` method.
The body typically contains one or more assertions which verify the outputs of
the system under test.
An assertion passes when its Boolean expression evaluates to `true` and fails otherwise.
A test passes when it reaches its end without any assertion failing;
if one or more assertions fail, the test itself fails.

An assertion may optionally include a message which will be printed in the
test report if the assertion fails.

```c++
WAYPOINT_AUTORUN(waypoint::TestRun const &t)
{
  auto const g1 = t.group("Group name 1");

  t.test(g1, "Test name 1")
    .run(
      [](waypoint::Context const &ctx)
      {
        ctx.assert(some_function(-1) != 0);
        ctx.assert(
          some_function(1) > 0,
          "Expected some_function(1) to return a positive value");
      });
}
```
