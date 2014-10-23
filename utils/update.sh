#!/bin/bash
printf "Attempting to update oxide...\n\n    Navigating to oxide directory\n"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

printf "    "
git pull
printf "\n"
read -t 10 -p "Hit ENTER to exit (closes automatically in 10 seconds)";