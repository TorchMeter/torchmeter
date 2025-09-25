#! /usr/bin/env bash

source "$(dirname "$0")/utils.sh"

# ---------------------------------------------------------------------------------------------------


if ! ROOT=$(find_dir 'torchmeter'); then 
    exit 1
else
    cd "$ROOT" || {
        red_output "Error: Cannot enter $ROOT"
        exit 1
    }
fi

if [[ -d "$ROOT/dist" ]]; then 
    rm -r "$ROOT/dist"
fi

activate_conda_env || exit 1

cyan_output "building..."
python -m build -v -n .