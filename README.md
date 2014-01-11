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

If you wish to set up a database, instead of using the default sqlite3 setup,
you can adapt the following to your situation:

```bash
export VOLUNTEER_DB_TYPE="django.db.backends.postgresql_psycopg2"
export VOLUNTEER_DB_HOST="127.0.0.1"
export VOLUNTEER_DB_NAME="volunteers"
export VOLUNTEER_DB_USER="fosdem"
export VOLUNTEER_DB_PASS="volunteers"
```

```bash
export VOLUNTEER_SESSION_SECRET="demo"
python manage.py syncdb
python manage.py migrate
python manage.py check_permissions
python manage.py runserver
firefox 127.0.0.1:8000
```
