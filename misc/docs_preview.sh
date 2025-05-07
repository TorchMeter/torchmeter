#! /usr/bin/env bash

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
        if os.system(f"pip list | grep '{dep}'"):
            print(dep)
except KeyError:
    sys.exit("Error: Missing [options.extras_require] or docs dependencies in setup.cfg")
EOF
)

    if [[ $? -ne 0 ]]; then
        red_output "Failed to parse setup.cfg"
        exit 1
    else 
        LACK=($LACK)
    fi

    for dep in "${Deps[@]}"; do
        if [[ -z "$dep" ]]; then
            continue
        fi
        
        pip install "$dep" || {
            red_output "Failed to install $dep"
            exit 1
        }
    done
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
ROOT=$(find_dir 'torchmeter')
if [[ $? -ne 0 ]]; then 
    exit 1
else
    cd $ROOT
fi

if [[ -d "$ROOT/dist" ]]; then 
    rm -r "$ROOT/dist"
fi

# activate conda env
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

# check dependencies
if [ "$QUICK_MODE" = false ]; then

    # Check Python dependencies
    cyan_output "\nChecking Python dependencies..."
    check_py_dependencies

    # Check Drawio
    cyan_output "\nChecking drawio..."
    check_drawio

    # Check xvfb
    cyan_output "\nChecking xvfb..."
    check_xvfb
    
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