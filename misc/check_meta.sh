#!/usr/bin/env bash

source "$(dirname "$0")/utils.sh"

# ---------------------------------------------------------------------------------------------------

if ROOT="$(find_dir 'torchmeter')"; then 
    cd "$ROOT" || {
        red_output "Error: Cannot enter $ROOT"
        exit 1
    }
else
    exit 1
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
if (( $(echo "$metadata_version > 1.2" | bc -l) )) && \
   [[ $(echo -e "$tar_requires_python\n$requires_python" | sort -V | head -n 1) == "3.8" ]]; then
    green_output "Metadata and requires-python are correct."
else
    red_output "Metadata or requires-python is incorrect."
fi

echo "----------------------------------------"
twine check --strict dist/*