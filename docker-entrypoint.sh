#!/bin/bash
set -e

if [ "$1" = 'run' ]; then
    exec python main.py "${@:2}"
elif [ "$1" = 'test' ]; then
    exec python -m unittest discover src/tests
else
    exec "$@"
fi