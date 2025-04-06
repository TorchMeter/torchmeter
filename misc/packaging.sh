#! /usr/bin/env bash

cyan_output() {
    echo -e "\033[36m$1\033[0m"
}

green_output() {
    echo -e "\033[32m$1\033[0m"
}

red_output() {
    echo -e "\033[31m$1\033[0m"
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

if [[ -d "$ROOT/dist" ]]; then 
    rm -r "$ROOT/dist"
fi

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

cyan_output "building..."
python -m build -v -n .