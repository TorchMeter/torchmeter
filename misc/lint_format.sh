#!/usr/bin/env bash

green_output() {
    echo -e "\033[32m$1\033[0m"
}

cyan_output() {
    echo -e "\033[36m\033[0m"
}

find_dir() {
    local target_path=$1
    local current_path=$(realpath $(dirname $0))
    local found_path=""

    while [ "$current_path" != "/" ]; do
        if [ -d "$current_path/$target_path" ]; then
            found_path="$current_path"
            break
        elif [ -f "$current_path/$target_path" ]; then
            found_path="$current_path"
            break
        fi
        current_path=$(dirname "$current_path")
    done

    if [ -z "$found_path" ]; then 
        echo "Error: $target_path not found!"
        exit 1
    else 
        echo $found_path
    fi
}

# ---------------------------------------------------------------------------------------------------

ROOT=$(find_dir 'torchmeter')
if [[ $? -ne 0 ]]; then 
    exit 1
else
    cd $ROOT
fi

# -------------------------------------- Activate Virtual Env ---------------------------------------

eval "$(conda shell.bash hook)"

envs=$(conda env list | grep -v "#" | cut -d " " -f1)

cyan_output "Available conda environments:"
PS3="Choose your Python env: "
select env in $envs
do
    if [ -n "$env" ]; then
        cyan_output "$env selected."
	conda activate "$env"
	green_output "$env activated.\n"
        break
    else
        red_output "Invalid selection. Please try again."
    fi
done

# --------------------------------------------- Format -----------------------------------------------

set +e
ruff format \
  --preview \
  --target-version=py38
exit_code=$?
set -e

if [[ $exit_code -eq 0 ]]; then
  echo -e "✅ Formatting finish! 🎉\n"
else
  echo -e "❌ Formatting failed! Some code does not meet the format requirements!s" >&2
  echo -e "❌ Ruff terminates abnormally due to invalid configuration, invalid CLI options, or an internal error" >&2
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
  echo -e "✅ Linting passed! Code quality check successful! 🎉\n"
else
  echo -e "❌ Linting failed! Some code does not meet the linting rules!\n" >&2
  exit 1
fi