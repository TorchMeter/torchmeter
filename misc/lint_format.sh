#!/usr/bin/env bash

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
	green_output "$env activated."
        break
    else
        red_output "Invalid selection. Please try again."
    fi
done

# ---------------------------------------------- Lint -----------------------------------------------

set +e
ruff check \
  --preview \
  --target-version=py38 \
  --output-format=grouped
exit_code=$?
set -e

if [[ $exit_code -eq 0 ]]; then
  echo -e "\n✅ Linting passed! Code quality check successful! 🎉"
else
  echo -e "\n❌ Linting failed! Some code does not meet the linting rules!" >&2
  exit 1
fi

# --------------------------------------------- Format -----------------------------------------------

set +e
ruff format \
  --diff \
  --preview \
  --target-version=py38
exit_code=$?

set -e
if [[ $exit_code -eq 0 ]]; then
  echo -e "\n✅ Formatting passed! All code is well-formated! 🎉"
else
  echo -e "\n❌ Formatting failed! Some code does not meet the format requirements!" >&2
  exit 1
fi