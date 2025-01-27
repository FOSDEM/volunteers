fosdem-volunteers
=================

![build](https://github.com/Logout22/volunteers/actions/workflows/main.yml/badge.svg)
![codecov](https://codecov.io/gh/Logout22/volunteers/graph/badge.svg)

Volunteers management system for conferences, originally written for FOSDEM.

Development setup
=================

The tool has been tested on Python3.10 and Python3.11. Python3.13 is not currently supported.
The production version of this uses Python3.11 (as of Jan 2025).

After cloning the repo do these steps:

1) Create a python environment using python3. 
   eg: `virtualenv -p /usr/bin/python3 ./venv`
   and activate this environment whenever working on the project (all other steps assume this)
   ```
   source ./venv/bin/activate
   ```

2) Install all dependencies in the environment:
   ```
   pip install -r requirements-dev.txt
   ```

3) create a `volunteer_mgmt/localsettings.py` file
   you can copy volunteer_mgmt/localsettings_example.py as a starting point.
   By default this uses a sqlite3 database.
   When running locally for development, make sure you add the line "DEBUG=True".

4) set up the initial database:
   ```
   ./manage.py migrate
   ```

5) make sure that all static files are collected
   ```
   ./manage.py collectstatic
   ```

6) create a superuser:
   ```
   ./manage.py createsuperuser
   ```

7) run a development server:
   ```
   ./manage.py runserver
   ```
   which should give you: http://localhost:8000/
8) in the admin interface http://localhost:8000/admin/ - make sure you create an edition before adding any other things


Production setup 
================
See [the playbook instructions](deployment/playbook/README.md) for more information.
