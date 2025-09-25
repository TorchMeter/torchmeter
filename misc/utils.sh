#!/usr/bin/env bash

# TorchMeter, AGPL-3.0 license
# Author: Ahzyuan
# Repo: https://github.com/TorchMeter/torchmeter

# ---------------------------- Colorful Output ----------------------------
cyan_output() {
    echo -e "\033[36m$1\033[0m"
}

yellow_output() {
    echo -e "\033[33m$1\033[0m"
}

green_output() {
    echo -e "\033[32m$1\033[0m"
}

red_output() {
    echo -e "\033[31m$1\033[0m"
}

# ---------------------------- Helper Functions ----------------------------

# Interactively activate a conda environment
# This function lists all available conda environments and allows user to select one
# Usage: activate_conda_env
# Dependencies: conda must be installed and available in PATH
# Side effects: 
#   - Activates the selected conda environment
#   - Exits with code 1 if activation fails or conda is not available
activate_conda_env() {
    eval "$(conda shell.bash hook)"

    envs=$(conda env list | grep -v "#" | cut -d " " -f1)

    cyan_output "Available conda environments:"
    PS3="Choose your Python env: "
    select env in $envs
    do
        if [ -n "$env" ]; then
            cyan_output "$env selected."
            conda activate "$env"  || {
                red_output "Error: Cannot activate $env"
                exit 1
            }
            green_output "$env activated."
            break
        else
            red_output "Invalid selection. Please try again."
        fi
    done
}

# Find the root directory containing a specific file or directory
# Searches upward from the script's location until it finds the target or reaches root
# Usage: find_dir "target_file_or_directory"
# Args:
#   $1: target_path - The file or directory name to search for
# Returns:
#   The absolute path of the directory containing the target
# Exit codes:
#   0: Success (target found)
#   1: Failure (target not found, reached filesystem root)
find_dir() {
    local target_path=$1
    local current_path found_path

    current_path=$(realpath "$(dirname "$0")")
    found_path=""

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
        echo "$found_path"
    fi
}