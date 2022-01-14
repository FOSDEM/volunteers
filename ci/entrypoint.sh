#!/bin/sh
set -o errexit
set -o nounset

utils/create-venv.sh
utils/install-dependencies.sh
utils/setup-file-system.sh
utils/setup-server.sh
utils/run-linter.sh
utils/run-tests.sh

