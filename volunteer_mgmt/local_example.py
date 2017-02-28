# Admins
ADMINS = (
    ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS


# Database config
# When on heroku
if dj_database_url.config():
    DATABASES = {}
    DATABASES['default'] = dj_database_url.config()
# When on localhost
else:
    DATABASES = {
        'default': {
            # 'django.db.backends.' +  'postgresql_psycopg2', 'mysql',
            # 'sqlite3' or 'oracle'.
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # Or path to database file if using sqlite3.
            'NAME': 'volunteers',
            'USER': 'volunteers',
            'PASSWORD': 'volunteers',
            # Empty for localhost through domain sockets or '127.0.0.1' for
            # localhost through TCP.
            'HOST': '127.0.0.1',
            # Set to empty string for default.
            'PORT': '5432',
        }
    }

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'demo'

# Volunteer sync
# Currently we only support petabarf.
SCHEDULE_SYNC_TYPE = 'pentabarf'
SCHEDULE_SYNC_URI = 'https://example.org/schedule/xml'

# Userena settings
EMAIL_PORT = 25
EMAIL_USE_TLS = True
EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = 'volunteers'
EMAIL_HOST_PASSWORD = 'volunteers'
DEFAULT_FROM_EMAIL = 'volunteers@example.com'
