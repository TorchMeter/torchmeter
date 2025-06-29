#!/usr/bin/env bash

red_output() {
    echo -e "\033[31m$1\033[0m" >&2
} 

green_output() {
    echo -e "\033[32m$1\033[0m"
}

# ---------------------------------------------------------------------------------------------------

PATTERN='^(depr|perf|feat|fix|docs|test|ci|chore|build|refactor|revert)(\([^ ]+\))?\!?\s?: [A-Z].*[^\.\!\?,…！？。， ]$'

if [ $# -ne 1 ]; then
  red_output "Error: There is and only needs one input, please enclose your input in '' and retry!"
  red_output "Usage: $0 'YOUR-PR-TITLE'" >&2
  exit 1
fi

input="$1"

if [ -z "$input" ]; then
  red_output "Error: Input cannot be empty!"
  exit 1
fi

if echo "$input" | grep -Eq "$PATTERN"; then
  green_output "Valid"
  exit 0
else
  red_output "Invalid"
  exit 1
fi