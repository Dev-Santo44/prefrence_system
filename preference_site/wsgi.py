"""WSGI config for preference_site project."""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "preference_site.settings")
application = get_wsgi_application()
