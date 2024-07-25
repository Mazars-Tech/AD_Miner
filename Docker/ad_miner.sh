#!/bin/bash
set -e

# Default report name
DEFAULT_REPORT_NAME="ADMiner"

# Check if the first argument is --rdp or another flag that doesn't indicate a report name
if [[ "$1" == --* ]]; then
    REPORT_NAME=$DEFAULT_REPORT_NAME
else
    # Check if a report name was provided, otherwise use default
    REPORT_NAME=${1:-$DEFAULT_REPORT_NAME}
    
    # Shift the first argument if it was provided
    if [ "$#" -gt 0 ]; then
        shift
    fi
fi

# Run AD_Miner with the provided arguments
exec python3 -m ad_miner -b "$BOLT_URL" -u "$USER_NEO" -p "$PASSWORD_NEO" -c -cf "$REPORT_NAME" "$@"
