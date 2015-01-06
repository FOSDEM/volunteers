fosdem-volunteers
=================

Volunteers management system for the FOSDEM conference

SETUP
=====
```bash
git clone https://github.com/jrial/fosdem-volunteers.git
cd fosdem-volunteers
sudo apt-get install libpq-dev
pip install -r requirements.txt
```

If you wish to set up a database, instead of using the default sqlite3 setup, you can adapt the following to your situation:

```bash
export VOLUNTEER_DB_USER="fosdem"
export VOLUNTEER_DB_HOST="127.0.0.1"
export VOLUNTEER_DB_NAME="volunteers"
export VOLUNTEER_DB_PASS="volunteers"
export VOLUNTEER_SESSION_SECRET="demo"
export VOLUNTEER_DB_TYPE="django.db.backends.postgresql_psycopg2"
```

If you need to test mail functionality (or don't want to get errors during signup), you also need to set up some SMTP variables:

```bash
export SMTP_PORT="25"
export SMTP_HOST="localhost"
export SMTP_FROM_EMAIL="me@example.com"
```

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

For production installations it's not recommended to run the development server, but run it behind a real webserver like Apache, Nginx, Lighthttpd, ... Instructions for setting this up can be found online.


DEVELOPMENT PITFALLS
====================

South:
------

* Sometimes South fails to create a schemamigration for a new field, with the puzzling error that the field does not exist. This happens when another model references the model in which the field has been added, using a default value. If this happens, remove the default value temporarily before you create the schemamigration, and re-add it after the SQL code has been generated.
