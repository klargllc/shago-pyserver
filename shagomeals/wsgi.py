"""
WSGI config for hotspot project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
# from django_forest import init_forest

from django.core.wsgi import get_wsgi_application



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shagomeals.settings')


# init_forest()
application = get_wsgi_application()
