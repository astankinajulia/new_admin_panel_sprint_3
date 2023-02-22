import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'movies_database'),
        'USER': os.environ.get('POSTGRES_USER', 'app'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'movies_database'),
        'HOST': os.environ.get('DB_HOST', 'postgres'),
        'PORT': os.environ.get('DB_PORT', 5432),
        'OPTIONS': {
           'options': '-c search_path=public,content'
        }
    }
}
