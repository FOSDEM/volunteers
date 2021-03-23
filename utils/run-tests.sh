#!/bin/sh
set -o errexit
set -o nounset

. venv/bin/activate
echo " ##### Run test #####"
coverage run manage.py test
coverage xml

