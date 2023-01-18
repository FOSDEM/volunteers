#!/bin/sh
set -o errexit
set -o nounset

cp volunteer_mgmt/localsettings_example.py volunteer_mgmt/localsettings.py

. venv/bin/activate
./manage.py migrate
./manage.py collectstatic
./manage.py createsuperuser --noinput --username test --email me@fosdem.org

