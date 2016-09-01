fosdem-volunteers
=================

Volunteers management system for conferences, originally written for FOSDEM.

SETUP
=====
```bash
git clone https://github.com/jrial/fosdem-volunteers.git
cd fosdem-volunteers
sudo apt-get install libpq-dev
```

It is advised to use virtualenv for the Python dependencies. Information on how
to set it up can be found online. If you don't use virtualenv, run the next
command through sudo:

```bash
pip install -r requirements.txt
```

Next, copy volunteer_mgmt/localsettings_example.py to
volunteer_mgmt/localsettings.py and edit to fit your needs. By default it's not
very secure, and uses a sqlite3 DB backend.

If you need to test mail functionality (or don't want to get errors during
signup), you also need to set up the SMTP variables in localsettings.py

Then do the initial setup:

```bash
python manage.py syncdb
python manage.py migrate
python manage.py check_permissions
```

And finally, launch the development server.

```bash
python manage.py runserver
firefox 127.0.0.1:8000
```

For production installations it's not recommended to run the development server,
but run it under gunicorn and behind a real webserver like Apache, Nginx,
Lighthttpd, ... Instructions can be found online.


DEVELOPMENT PITFALLS
====================

South:
------

* Sometimes South fails to create a schemamigration for a new field, with the
puzzling error that the field does not exist. This happens when another model
references the model in which the field has been added, using a default value.
If this happens, remove the default value temporarily before you create the
schemamigration, and re-add it after the SQL code has been generated.
