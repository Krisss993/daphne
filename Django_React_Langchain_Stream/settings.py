import os
import dj_database_url

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'ml-chat.onrender.com']

CSRF_TRUSTED_ORIGINS = ['https://ml-chat.onrender.com']

CORS_ALLOW_ALL_ORIGINS = True

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]


ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'optional'
LOGIN_REDIRECT_URL = '/'
SITE_ID = 1
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'langchain_stream',
    'langchain_chat',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'staff',
    'core',
    'crispy_forms',
    'crispy_bootstrap4',
    'cart',
    'ml',
    'corsheaders',


]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]


ROOT_URLCONF = 'Django_React_Langchain_Stream.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI_APPLICATION = 'Django_React_Langchain_Stream.wsgi.application'
ASGI_APPLICATION = "Django_React_Langchain_Stream.asgi.application"










# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}
# print(f"postgresql://{os.environ.get('DATABASE_USER')}:{os.environ.get('DATABASE_PASSWORD')}@{os.environ.get('DATABASE_PORT')}/{os.environ.get('DATABASE_NAME')}")

# DATABASES = {
#     'default': dj_database_url.config(default=f"postgresql://{os.environ.get('DATABASE_USER')}:{os.environ.get('DATABASE_PASSWORD')}@{os.environ.get('DATABASE_HOST')}:{os.environ.get('DATABASE_PORT')}/{os.environ.get('DATABASE_NAME')}")
# }










# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = '/static/'
# Directory where static files are collected from apps and other locations
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # The folder in your project for static files
]
# Directory where static files are collected by `collectstatic` during production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Media files configuration
MEDIA_URL = '/media/'  # The base URL to serve media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'


# if DEBUG is False:
#    SESSION_COOKIE_SECURE = True
#    SECURE_BROWSER_XSS_FILTER = True
#    SECURE_CONTENT_TYPE_NOSNIFF = True
#    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#    SECURE_HSTS_SECONDS = 31536000
#    SECURE_REDIRECT_EXEMPT = []
#    SECURE_SSL_REDIRECT = True
#    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDER_PROTO', 'https')

#    ALLOWED_HOSTS = ['www.domain.com']
#    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


CRISPY_TEMPLATE_PACK = 'bootstrap4'

# DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
# NOTIFY_EMAIL = env('NOTIFY_EMAIL')

# PAYPAL_CLIENT_ID = env('PAYPAL_SANDBOX_CLIENT_ID')
# PAYPAL_SECRET_KEY = env('PAYPAL_SANDBOX_SECRET_KEY')
# SECURE_CROSS_ORIGIN_OPENER_POLICY='same-origin-allow-popups'


USE_X_FORWARDED_HOST = True