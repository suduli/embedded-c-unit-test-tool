# Real GCC 14.4.0 coverage output

Captured 2026-11-27 with the official `gcc:14` container image, no network:

    gcc --coverage -fcondition-coverage -O0 -c NAME.c -o NAME.o
    gcc --coverage NAME.o -o NAME && ./NAME
    gcov --conditions -b --json-format NAME.o

The `.gcov.json` files are the decompressed gcov output, re-indented with sorted keys.

Observed: a decision with 64 conditions is measured; with 65 conditions GCC warns
`Too many conditions (found 65); giving up coverage [-Wcoverage-too-many-conditions]`
and the line carries no condition records.
