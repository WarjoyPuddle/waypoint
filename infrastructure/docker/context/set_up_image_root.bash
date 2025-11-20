# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

set -euo pipefail

function prepare_apt
{
  apt-get update

  apt-get upgrade \
    --with-new-pkgs \
    --yes
}

function set_timezone
{
  local timezone="$1"

  ln \
    --force \
    --symbolic \
    "/usr/share/zoneinfo/${timezone}" \
    "/etc/localtime"
  echo "${timezone}" >"/etc/timezone"

  apt-get install \
    --yes \
    tzdata
}

function create_user
{
  local uid="$1"
  local gid="$2"
  local username="$3"

  apt-get install --yes \
    adduser

  userdel ubuntu || true
  rm -rf /home/ubuntu

  addgroup --gid "${gid}" "${username}"
  adduser \
    --disabled-password \
    --shell /bin/bash \
    --gecos "" \
    --uid "${uid}" \
    --gid "${gid}" \
    "${username}"
}

function install_apps
{
  apt-get install --yes \
    bash \
    binutils \
    black \
    build-essential \
    clang-20 \
    clang-tools-20 \
    clang-format-20 \
    clang-tidy-20 \
    cmake \
    cmake-format \
    gcc-15 \
    g++-15 \
    gcovr \
    gdb \
    git \
    make \
    ninja-build \
    python3.13 \
    python3-isort \
    valgrind \
    vim
}

function add_kitware_apt_repo
{
  local keyring_path="/usr/share/keyrings/kitware-archive-keyring.gpg"

  apt-get install --yes ca-certificates gpg wget
  test -f /usr/share/doc/kitware-archive-keyring/copyright ||
    wget -O - https://apt.kitware.com/keys/kitware-archive-latest.asc 2>/dev/null |
	  gpg --dearmor - |
	  tee "${keyring_path}" >/dev/null
  echo "deb [signed-by=${keyring_path}]" \
    "https://apt.kitware.com/ubuntu/ noble main" |
    tee /etc/apt/sources.list.d/kitware.list >/dev/null
  apt-get update
}

function main
{
  local uid="$1"
  local gid="$2"
  local username="$3"
  local timezone="$4"

  prepare_apt
  set_timezone \
    "${timezone}"
  create_user \
    "${uid}" \
    "${gid}" \
    "${username}"
  add_kitware_apt_repo
  install_apps

  ln --force --symbolic /usr/bin/gcov-15 /usr/bin/gcov
}

main "$1" "$2" "$3" "$4"
