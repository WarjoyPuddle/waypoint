# Copyright (c) 2025-2026 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

cmake_minimum_required(VERSION 4.0)

# CMake 4.2.2
set(CMAKE_EXPERIMENTAL_CXX_IMPORT_STD "d0edc3af-4c50-42ea-a356-e2862fe7a444")

project(
  project_module_test
  VERSION 0.0.1
  DESCRIPTION "Playing with C++23 modules"
  LANGUAGES CXX)

cmake_path(SET PROJECT_ROOT_DIR NORMALIZE ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(module_test ${PROJECT_ROOT_DIR}/main.cpp)

target_compile_features(module_test PRIVATE cxx_std_23)

if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
  # Breaks Clang-20 & 'Ninja Multi-Config' generator on Ubuntu Linux
  set_target_properties(module_test PROPERTIES CXX_EXTENSIONS FALSE)
endif()

if(CMAKE_GENERATOR STREQUAL "Ninja Multi-Config")
  # Required for GCC-15 & 'Ninja Multi-Config' generator on Ubuntu Linux;
  # Required for Clang-20 & 'Ninja Multi-Config' generator on Ubuntu Linux;
  # Required for VS2026 & 'Ninja Multi-Config' generator on Windows 11;
  # Breaks (but also not required) for VS2026 & 'Visual Studio 18 2026' generator on Windows 11.
  set_target_properties(module_test PROPERTIES CXX_MODULE_STD TRUE)
endif()

target_sources(
  module_test
  PRIVATE FILE_SET
          module_test_modules
          TYPE
          CXX_MODULES
          BASE_DIRS
          ${PROJECT_ROOT_DIR}
          FILES
          ${PROJECT_ROOT_DIR}/lib.cpp)

# ???
# linux gcc 15 with ninja mc
# rm -rf ./build___ && CC=gcc-15 CXX=g++-15 cmake -Wno-dev -S. -B./build___ -G"Ninja Multi-Config" && cmake --build ./build___ --config Debug && cmake --build ./build___ --config RelWithDebInfo && cmake --build ./build___ --config Release && ./build___/Debug/module_test && ./build___/RelWithDebInfo/module_test && ./build___/Release/module_test

# linux clang 20 with ninja mc
# rm -rf ./build___ && CC=clang-20 CXX=clang++-20 cmake -Wno-dev -S. -B./build___ -G"Ninja Multi-Config" && cmake --build ./build___ --config Debug && cmake --build ./build___ --config RelWithDebInfo && cmake --build ./build___ --config Release && ./build___/Debug/module_test && ./build___/RelWithDebInfo/module_test && ./build___/Release/module_test

# windows MSVC with VS2026 generator in cmd prompt
# rmdir /S /Q .\build___ & cmake -Wno-dev -S. -B./build___ -G"Visual Studio 18 2026" && cmake --build ./build___ --config Debug && cmake --build ./build___ --config RelWithDebInfo && cmake --build ./build___ --config Release && .\build___\Debug\module_test && .\build___\RelWithDebInfo\module_test && .\build___\Release\module_test

# windows MSVC with ninja in cmd prompt
# "C:\Program Files\Microsoft Visual Studio\18\Professional\VC\Auxiliary\Build\vcvarsall.bat" x64 10.0.26100.0
# rmdir /S /Q .\build___ & cmake -Wno-dev -S. -B./build___ -G"Ninja Multi-Config" && cmake --build ./build___ --config Debug && cmake --build ./build___ --config RelWithDebInfo && cmake --build ./build___ --config Release && .\build___\Debug\module_test && .\build___\RelWithDebInfo\module_test && .\build___\Release\module_test

# windows Clang 21.1.8 with ninja in cmd prompt
# rmdir /S /Q .\build___ & cmake -Wno-dev -S. -B./build___ -G"Ninja Multi-Config" && cmake --build ./build___ --config Debug && cmake --build ./build___ --config RelWithDebInfo && cmake --build ./build___ --config Release && .\build___\Debug\module_test && .\build___\RelWithDebInfo\module_test && .\build___\Release\module_test



# Remove-Item -Force -Recurse ./build___ ; cmake -Wno-dev -S. -B./build___ -G"Visual Studio 18 2026" && cmake --build ./build___ --config Debug && cmake --build ./build___ --config RelWithDebInfo && cmake --build ./build___ --config Release && ./build___/Debug/module_test && ./build___/RelWithDebInfo/module_test && ./build___/Release/module_test

# function Invoke-CmdScript {
#   param(
#     [String] $scriptName
#   )
#   $cmdLine = """$scriptName"" $args & set"
#   & $Env:SystemRoot\system32\cmd.exe /c $cmdLine |
#   select-string '^([^=]*)=(.*)$' | foreach-object {
#     $varName = $_.Matches[0].Groups[1].Value
#     $varValue = $_.Matches[0].Groups[2].Value
#     set-item Env:$varName $varValue
#   }
# }
# Invoke-CmdScript 'C:\Program Files\Microsoft Visual Studio\18\Professional\VC\Auxiliary\Build\vcvarsall.bat' x64 10.0.26100.0
# Remove-Item -Force -Recurse ./build6___ ; cmake -S. -B./build6___ -G'Ninja Multi-Config' && cmake --build ./build6___ --config Debug && cmake --build ./build6___ --config RelWithDebInfo && cmake --build ./build6___ --config Release && ./build6___/Debug/module_test.exe && ./build6___/RelWithDebInfo/module_test.exe && ./build6___/Release/module_test.exe

#[[
C:\dev\git\waypoint>rmdir /S /Q .\build___ & cmake -Wno-dev -S. -B./build___ -G"Visual Studio 18 2026" && cmake --build ./build___ --config Debug && cmake --build ./build___ --config RelWithDebInfo && cmake --build ./build___ --config Release && .\build___\Debug\module_test && .\build___\RelWithDebInfo\module_test && .\build___\Release\module_test
-- Selecting Windows SDK version 10.0.26100.0 to target Windows 10.0.22631.
-- The CXX compiler identification is MSVC 19.50.35723.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: C:/Program Files/Microsoft Visual Studio/18/Professional/VC/Tools/MSVC/14.50.35717/bin/Hostx64/x64/cl.exe - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Configuring done (3.9s)
CMake Error in CMakeLists.txt:
  The "CXX_MODULE_STD" property on the target "module_test" requires that the
  "__CMAKE::CXX23" target exist, but it was not provided by the toolchain.
  Reason:

    Unsupported generator: Visual Studio 18 2026


-- Generating done (0.0s)
CMake Generate step failed.  Build files cannot be regenerated correctly.
#]]
