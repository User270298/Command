#!/usr/bin/python3
import os
import sys
import logging
import traceback

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

try:
    # Добавляем путь к проекту
    project_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_path)
    logger.info(f"Added project path: {project_path}")
    logger.info(f"Python path: {sys.path}")

    # Устанавливаем переменные окружения
    os.environ['DJANGO_SETTINGS_MODULE'] = 'equipment_tracking.settings'
    os.environ['PYTHONPATH'] = project_path
    logger.info("Set Django settings module")

    # Импортируем и запускаем WSGI-приложение
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    logger.info("WSGI application initialized successfully")

except Exception as e:
    logger.error(f"Error initializing application: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise 