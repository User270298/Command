# Приложение для Учета Настройки Оборудования

Система для учета и отслеживания настройки оборудования выездными группами.

## Возможности

- Регистрация пользователей и управление ролями (старший группы)
- Создание командировок и управление членами группы
- Добавление организаций для обслуживания
- Учет настройки оборудования по разным типам измерений
- Формирование отчетов PDF по каждому сотруднику
- Выгрузка общих данных в Excel
- Автоматическое напоминание о необходимости повторной авторизации (если не заходили более 5 дней)

## Установка и запуск

1. Клонировать репозиторий
2. Установить зависимости:
   ```
   pip install django djangorestframework djangorestframework-simplejwt pillow django-cors-headers pandas xlsxwriter reportlab
   ```
3. Применить миграции:
   ```
   python manage.py migrate
   ```
4. Создать суперпользователя (администратора):
   ```
   python manage.py createsuperuser
   ```
5. Запустить сервер разработки:
   ```
   python manage.py runserver
   ```

## API Endpoints

### Аутентификация
- `/api/users/token/` - Получение JWT-токена
- `/api/users/token/refresh/` - Обновление JWT-токена

### Пользователи
- `/api/users/users/` - Список пользователей
- `/api/users/users/me/` - Информация о текущем пользователе
- `/api/users/users/team_members/` - Список всех доступных членов команды

### Командировки
- `/api/trips/trips/` - Управление командировками
- `/api/trips/trips/{id}/close_trip/` - Закрытие командировки
- `/api/trips/trips/active_trip/` - Получение активной командировки

### Организации
- `/api/trips/organizations/` - Управление организациями
- `/api/trips/organizations/{id}/close_organization/` - Закрытие организации

### Типы измерений и оборудование
- `/api/equipment/measurement-types/` - Управление типами измерений
- `/api/equipment/equipment-records/` - Управление записями об оборудовании
- `/api/equipment/equipment-records/by_organization/` - Получение записей по организации
- `/api/equipment/equipment-records/by_user/` - Получение записей по пользователю

### Отчеты
- `/api/equipment/equipment-records/generate_user_report/` - PDF отчет по пользователю
- `/api/equipment/equipment-records/generate_organization_report/` - PDF отчет по организации
- `/api/equipment/equipment-records/export_excel/` - Выгрузка в Excel 