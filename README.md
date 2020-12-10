fosdem-volunteers
=================

Volunteers management system for conferences, originally written for FOSDEM.

Development setup
=================

After cloning the repo do these steps:


1) Create a python environment using python 2.7 (we are about to update that)
   eg: `virtualenv -p /usr/bin/python2.7 ./venv`
   and activate this environment whenever working on the project (all other steps assume this)
   ```
   ./venv/bin/activate
   ```

2) Install all dependencies in the environment:
   ```
   pip install -r requirements.txt
   ```

3) create a `volunteer_mgmt/localsettings.py` file
   you can copy volunteer_mgmt/localsettings_example.py as a starting point.
   By default this uses a sqlite3 database.

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
