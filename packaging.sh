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

DIR=$(dirname "$(readlink -f "$0")")

if [[ -d "$DIR/dist" ]]; then 
    rm -r "$DIR/dist"
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