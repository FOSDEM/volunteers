import dj_database_url

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Admins
ADMINS = (
    ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
# Allow all host headers
ALLOWED_HOSTS = ['127.0.0.1']

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

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Brussels'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# Volunteer sync
# Currently we only support petabarf.
SCHEDULE_SYNC_TYPE = 'pentabarf'
SCHEDULE_SYNC_URI = 'https://example.org/schedule/xml'

ROOMS_HERALDING_REQUIRED = ['Janson', 'K.1.105 (La Fontaine)']
ROOMS_VIDEO_NEEDED = ['Janson', 'K.1.105 (La Fontaine)']

# Userena settings
EMAIL_PORT = 25
EMAIL_USE_TLS = True
EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = 'volunteers'
EMAIL_HOST_PASSWORD = 'volunteers'
DEFAULT_FROM_EMAIL = 'volunteers@example.com'
