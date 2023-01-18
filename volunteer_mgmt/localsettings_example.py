USE_X_FORWARDED_HOST = True

# Admins
MANAGERS = ADMINS = (
    ('Me', 'me@fosdem.org')
)


# Database config
# When on heroku
if 'dj_database_url' in locals() and dj_database_url.config():
    DATABASES = {}
    DATABASES['default'] = dj_database_url.config()
# When on localhost
else:
    DATABASES = {
        'default': {
            # 'django.db.backends.' +  'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'volunteers.db',
            # Replace above with below for a local postgres DB (which you'll need to supply)
            # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # 'NAME': 'volunteers',
            # 'USER': 'volunteers',
            # 'PASSWORD': 'volunteers',
            # 'HOST': '127.0.0.1'
            # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
            # Set to empty string for default.
            # 'PORT': '5432',
        },
        'pentabarf': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'penta.db',
            # Replace above with below for a local postgres DB (which you'll need to supply)
            # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # 'NAME': 'penta',
            # 'USER': 'volunteers',
            # 'PASSWORD': 'volunteers',
            # 'HOST': '127.0.0.1'
        }
    }

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'VERY_SECRET'

# Volunteer sync
# Currently we only support petabarf.
SCHEDULE_SYNC_TYPE = 'pentabarf'
SCHEDULE_SYNC_URI = 'https://fosdem.org/schedule/xml'

# Userena settings
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_HOST = '127.0.0.1'
DEFAULT_FROM_EMAIL = 'volunteer-admin@lists.fosdem.org'

SETUP_FOR_CURRENT_YEAR_COMPLETE = True
IMPORT_VIDEO_TASKS = False
