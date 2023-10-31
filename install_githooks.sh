#!/bin/bash

# Linux only
# Git hooks will scan staged files to prevent commits of sensitive files
# For more info, inspect "git_hooks/pre-commit"

echo "## ADMiner git hooks installer ##"
echo ""

potential_python_path=("python3" "python3.10" "python")

# Initialize the Python path
python_path=""

for potential_executable in "${potential_python_path[@]}"; do
    path=$(command -v "$potential_executable")
    if [ -n "$path" ]; then
        python_path="$path"
        break
    fi
done

# Check Python version
if [ -n "$python_path" ]; then
    python_version=$("$python_path" --version 2>&1)
    if [[ $python_version == *"Python 3.10"* ]]; then
	echo "- If pre-commit hook fails, replace first line of ./git_hooks/pre-commit with #!$python_path"
	echo ""
    fi
fi

# Install hooks
root="$(pwd)"
echo -ne "- Creating symlink: " && ln -s "$root/git_hooks/pre-commit" "$root/.git/hooks" -v
