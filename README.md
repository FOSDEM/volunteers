fosdem-volunteers
=================

Volunteers management system for the FOSDEM conference

SETUP
=====
```bash
git clone https://github.com/jrial/fosdem-volunteers.git
cd fosdem-volunteers
pip install -r requirements.txt
python manage.py syncdb
python manage.py migrate
python manage.py runserver
firefox 127.0.0.1:8000
```

CREDITS ^_^
===========
* Django developers
* postgre developers
