#!/usr/bin/python3
import os
import sys

# Add your project directory to the Python path
sys.path.insert(0, '/home/o/ovsyan_93/metrotrip.ru/public_html')

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'command_project.settings'

# Import and run the WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 