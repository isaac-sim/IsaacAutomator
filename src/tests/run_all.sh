#!/bin/sh
# Run all unit tests inside the Isaac Automator container.
# Filenames use the *.test.py convention which unittest discovery does not
# accept as importable modules, so we invoke each file directly.

set -e

SELF_DIR="$(cd "$(dirname "$0")" && pwd -P)"

failed=0
for test_file in "${SELF_DIR}"/*.test.py; do
    [ -e "${test_file}" ] || continue
    echo "=== Running ${test_file##*/} ==="
    if ! python3 "${test_file}"; then
        failed=1
    fi
done

exit "${failed}"
