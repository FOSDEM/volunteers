#!/bin/sh
set -o errexit
set -o nounset

. venv/bin/activate
echo " ##### Run linter #####"
DJANGO_SETTINGS_MODULE=volunteer_mgmt.settings pylint --load-plugins pylint_django --fail-under=7 volunteers/

