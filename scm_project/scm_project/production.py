from .settings import *
import os

# Configure the domain name using the environment variable
# that Azure automatically creates for us.
ALLOWED_HOSTS = [os.environ['WEBSITE_HOSTNAME']] if 'WEBSITE_HOSTNAME' in os.environ else []

MIDDLEWARE = [                                                                   
    'django.middleware.security.SecurityMiddleware',                
]


# DBHOST is only the server name, not the full URL
hostname = os.environ['DBHOST']

# Configure Postgres database; the full username is username@servername,
# which we construct using the DBHOST value.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DBNAME'],
        'HOST': hostname + ".postgres.database.azure.com",
        'USER': os.environ['DBUSER'] + "@" + hostname,
        'PASSWORD': os.environ['DBPASS'] 
    }
}