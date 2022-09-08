#!/bin/sh -e
set -x

flake8 .
isort .
black --line-length 79 .
mypy --ignore-missing-imports app
