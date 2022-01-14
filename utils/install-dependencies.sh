#!/bin/sh
set -o errexit
set -o nounset

. venv/bin/activate
pip install -r requirements-dev.txt

