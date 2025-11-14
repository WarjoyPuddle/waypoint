# Copyright (c) 2025 Wojciech Kałuża
# SPDX-License-Identifier: MIT
# For license details, see LICENSE file

FROM ubuntu:25.04 AS base

SHELL ["/bin/bash", "-c"]

ARG DOCKER_UID
ARG DOCKER_GID
ARG DOCKER_USERNAME
ARG DOCKER_HOST_TIMEZONE="Etc/UTC"

ARG _HOME="/home/$DOCKER_USERNAME"
ARG _TEMP_DIR_ROOT="/docker_root_build_temp"
ARG _TEMP_DIR_USER="$_HOME/docker_user_build_temp"
ARG _SETUP_SCRIPT_ROOT="$_TEMP_DIR_ROOT/set_up_image_root.bash"
ARG _SETUP_SCRIPT_USER="$_TEMP_DIR_USER/set_up_image_user.bash"

ENV PATH=$PATH:$_HOME/.local/bin

USER root
COPY "./" $_TEMP_DIR_ROOT/
RUN bash $_SETUP_SCRIPT_ROOT \
$DOCKER_UID \
$DOCKER_GID \
$DOCKER_USERNAME \
$DOCKER_HOST_TIMEZONE
RUN rm -rf $_TEMP_DIR_ROOT/

USER $DOCKER_USERNAME
COPY --chown=$DOCKER_USERNAME "./" $_TEMP_DIR_USER/
RUN bash $_SETUP_SCRIPT_USER
RUN rm -rf $_TEMP_DIR_USER/
