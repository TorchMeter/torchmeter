#!/usr/bin/env bash

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