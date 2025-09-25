#! /usr/bin/env bash

# TorchMeter, AGPL-3.0 license
# Author: Ahzyuan
# Repo: https://github.com/TorchMeter/torchmeter

source "$(dirname "$0")/utils.sh"

check_py_dependencies() {

    LACK=$(python - <<EOF
import sys, os, re
import configparser
import importlib.util

config = configparser.ConfigParser()
config.read("setup.cfg")

try:
    deps = config["options.extras_require"]["docs"].strip()
    for dep in deps.split('\n'):
        dep = re.findall(r"(\w+)(\[.+\])?", dep)[0][0]
        if os.system(f"pip list | grep '{dep}' > /dev/null"):
            print(dep)
except KeyError:
    sys.exit("Error: Missing [options.extras_require] or docs dependencies in setup.cfg")
EOF
)

    # shellcheck disable=SC2181
    if [[ $? -ne 0 ]]; then
        red_output "Failed to parse setup.cfg"
        exit 1
    fi

    if [[ -n "$LACK" ]]; then
        LACK=("$LACK")
        for dep in "${LACK[@]}"; do
            if [[ -z "$dep" ]]; then
                continue
            fi
            
            pip install "$dep" || {
                red_output "Failed to install $dep"
                exit 1
            }
        done
    fi
    green_output "All docs dependencies have been installed."

}

check_drawio() {

    if ! command -v drawio &> /dev/null; then
        red_output "drawio command not found. Please install drawio first."
        cyan_output "You can install it via:"
        echo "sudo apt install draw.io  # Debian/Ubuntu"
        echo "or download from: https://github.com/jgraph/drawio-desktop/releases"
        exit 1
    else
        green_output "Drawio is installed."
    fi

}

check_xvfb() { 

    if ! dpkg-query -W -f='${Status}' 'xvfb' 2>/dev/null | grep -q "install ok installed"; then
        red_output "Missing system packages: xvfb"
        cyan_output "Please install it using:"
        echo "sudo apt update && sudo apt install -y xvfb"
        exit 1
    else
        green_output "All required system packages are installed."
    fi

}


# ---------------------------------------------------------------------------------------------------

# resolve pass-in arguments
QUICK_MODE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -q|--quick)
            QUICK_MODE=true
            shift
            ;;
        *)
            echo "Unknown parameter passed: $1"
            exit 1
            ;;
    esac
done

# navigate to project root
if ! ROOT="$(find_dir 'torchmeter')"; then 
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

# activate conda env
activate_conda_env || exit 1

# check dependencies
if [ "$QUICK_MODE" = false ]; then

    # Check Python dependencies
    cyan_output "\nChecking Python dependencies..."
    check_py_dependencies

    # # Check Drawio
    # cyan_output "\nChecking drawio..."
    # check_drawio

    # # Check xvfb
    # cyan_output "\nChecking xvfb..."
    # check_xvfb
    
else
    yellow_output "Quick mode enabled: skipping all dependency checks."
fi

# build docs & deploy locally
PORT=8000
while netstat -tuln | grep -q $PORT; do
    PORT=$((PORT+1))
done
cyan_output "\nDeploying docs on port $PORT..."
# xvfb-run -a mkdocs serve --dirtyreload -a "127.0.0.1:$PORT"
mkdocs serve --dirtyreload -a "127.0.0.1:$PORT"