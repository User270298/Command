import os
import django
import sys

# Добавляем родительскую директорию в путь Python
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Django_command.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def create_test_users():
    test_users = [
        {
            'username': 'senior1',
            'email': 'senior1@example.com',
            'password': 'senior123',
            'is_staff': True,
            'is_senior': True,
            'first_name': 'Иван',
            'last_name': 'Петров',
        },
        {
            'username': 'senior2',
            'email': 'senior2@example.com',
            'password': 'senior123',
            'is_staff': True,
            'is_senior': True,
            'first_name': 'Алексей',
            'last_name': 'Сидоров',
        },
        {
            'username': 'worker1',
            'email': 'worker1@example.com',
            'password': 'worker123',
            'is_staff': False,
            'is_senior': False,
            'first_name': 'Сергей',
            'last_name': 'Иванов',
        },
        {
            'username': 'worker2',
            'email': 'worker2@example.com',
            'password': 'worker123',
            'is_staff': False,
            'is_senior': False,
            'first_name': 'Дмитрий',
            'last_name': 'Козлов',
        },
        {
            'username': 'worker3',
            'email': 'worker3@example.com',
            'password': 'worker123',
            'is_staff': False,
            'is_senior': False,
            'first_name': 'Андрей',
            'last_name': 'Смирнов',
        },
    ]

    for user_data in test_users:
        if not User.objects.filter(username=user_data['username']).exists():
            User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                is_staff=user_data.get('is_staff', False),
                is_superuser=False,
                is_senior=user_data['is_senior'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                last_login_date=timezone.now()
            )
            print(f'Успешно создан пользователь {user_data["username"]} ({user_data["first_name"]} {user_data["last_name"]})')
        else:
            print(f'Пользователь {user_data["username"]} уже существует')

if __name__ == '__main__':
    create_test_users()