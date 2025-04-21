#!/usr/bin/env bash

red_output() {
    echo -e "\033[31m$1\033[0m"
} 

green_output() {
    echo -e "\033[32m$1\033[0m"
}

yellow_output() {
    echo -e "\033[33m$1\033[0m"
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

if [[ ! -d "$ROOT/dist" ]]; then 
    red_output "No dist folder found. Run 'bash misc/packaging.sh' first"
    exit 1
fi

requires_python=$(grep 'python_requires' setup.cfg | rev | cut -d'=' -f1 | rev)

tar_output=$(tar xfO dist/*.tar.gz)

metadata_version=$(echo "$tar_output" | grep 'Metadata-Version:' | head -n 1 | rev | cut -d' ' -f1 | rev)
tar_requires_python=$(echo "$tar_output" | grep 'Requires-Python:' | head -n 1 |cut -d'=' -f2)

echo -e "Metadata_version: $metadata_version $(yellow_output '(need >=1.2)')"
echo -e "Python Required: $tar_requires_python $(yellow_output "(need >=$requires_python)")"
echo "----------------------------------------"
if [[ "$metadata_version" > "1.2" ]] && \
   [[ $(echo -e "$tar_requires_python\n$requires_python" | sort -V | head -n 1) == "3.8" ]]; then
    green_output "Metadata and requires-python are correct."
else
    red_output "Metadata or requires-python is incorrect."
fi

echo "----------------------------------------"
twine check --strict dist/*