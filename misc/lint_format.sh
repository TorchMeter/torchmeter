#!/usr/bin/env bash

# TorchMeter, AGPL-3.0 license
# Author: Ahzyuan
# Repo: https://github.com/TorchMeter/torchmeter

source "$(dirname "$0")/utils.sh"

if ! ROOT="$(find_dir 'torchmeter')"; then 
    exit 1
else
    cd "$ROOT" || {
        red_output "Error: Cannot enter $ROOT"
        exit 1
    }
fi

# -------------------------------------- Activate Virtual Env ---------------------------------------
activate_conda_env || exit 1

# --------------------------------------------- Format -----------------------------------------------

set +e
ruff format \
  --preview \
  --target-version=py38
exit_code=$?
set -e

if [[ $exit_code -eq 0 ]]; then
  green_output "✅ Formatting finish! 🎉\n"
else
  red_output "❌ Formatting failed! Some code does not meet the format requirements!s" >&2
  red_output "❌ Ruff terminates abnormally due to invalid configuration, invalid CLI options, or an internal error" >&2
  exit 1
fi

# ---------------------------------------------- Lint -----------------------------------------------

set +e
ruff check \
  --preview \
  --fix \
  --unsafe-fixes \
  --target-version=py38 \
  --output-format=grouped
exit_code=$?
set -e

if [[ $exit_code -eq 0 ]]; then
  green_output "✅ Linting passed! Code quality check successful! 🎉\n"
else
  red_output "❌ Linting failed! Some code does not meet the linting rules!\n" >&2
  exit 1
fi