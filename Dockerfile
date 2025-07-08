# Используем официальный Python-образ
FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# Установим зависимости
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем код
COPY . /app/

# Команда запуска
CMD ["gunicorn", "--chdir", "/app", "Django_command.wsgi:application", "--bind", "0.0.0.0:8000"]
