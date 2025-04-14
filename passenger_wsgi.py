# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, '/app')
sys.path.insert(1, '/usr/local/lib/python3.9/site-packages')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Django_command.settings'
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 