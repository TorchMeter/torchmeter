#!/usr/bin/env bash

DIR=$(dirname "$(readlink -f "$0")")

if [[ ! -d "$DIR/dist" ]]; then 
    echo "\033[31mNo dist folder found. Run 'bash packaging.sh' first\033[0m"
    exit 1
fi

requires_python=$(grep 'python_requires' setup.cfg | rev | cut -d'=' -f1 | rev)

tar_output=$(tar xfO dist/*.tar.gz)

metadata_version=$(echo "$tar_output" | grep 'Metadata-Version:' | head -n 1 | rev | cut -d' ' -f1 | rev)
tar_requires_python=$(echo "$tar_output" | grep 'Requires-Python:' | head -n 1 |cut -d'=' -f2)

echo -e "Metadata_version: $metadata_version \033[31m(need >=1.2)\033[0m"
echo -e "Python Required: $tar_requires_python \033[31m(need $requires_python)\033[0m"
echo "----------------------------------------"
if [[ "$metadata_version" > "1.2" ]] && [[ "$tar_requires_python" == "$requires_python" ]]; then
    echo -e "Metadata and requires-python are \033[32mcorrect\033[0m."
else
    echo -e "Metadata or requires-python is \033[31mincorrect\033[0m."
fi

echo "----------------------------------------"
twine check --strict dist/*