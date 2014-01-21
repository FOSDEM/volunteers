fosdem-volunteers
=================

Volunteers management system for the FOSDEM conference

SETUP
=====
```bash
git clone https://github.com/jrial/fosdem-volunteers.git
cd fosdem-volunteers
pip install -r requirements.txt
```

If you wish to set up a database, instead of using the default sqlite3 setup, you can adapt the following to your situation:

```bash
export VOLUNTEER_DB_TYPE="django.db.backends.postgresql_psycopg2"
export VOLUNTEER_DB_HOST="127.0.0.1"
export VOLUNTEER_DB_NAME="volunteers"
export VOLUNTEER_DB_USER="fosdem"
export VOLUNTEER_DB_PASS="volunteers"
export VOLUNTEER_SESSION_SECRET="demo"
```

If you need to test mail functionality (or don't want to get errors during signup), you also need to set up some SMTP variables:

```bash
export SMTP_HOST="localhost"
export SMTP_FROM_EMAIL="me@example.com"
export SMTP_PORT="25"
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
