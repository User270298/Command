from django.db import migrations

def create_missing_tables(apps, schema_editor):
    # Создать таблицу trips_technicalstaffrecord, если не существует
    schema_editor.execute("""
        CREATE TABLE IF NOT EXISTS trips_technicalstaffrecord (
            id BIGSERIAL PRIMARY KEY,
            week DATE NOT NULL,
            value INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            organization_id BIGINT NOT NULL REFERENCES trips_organization(id),
            user_id BIGINT NOT NULL REFERENCES users_user(id)
        );
    """)
    # Добавить столбец senior_id, если не существует
    schema_editor.execute("""
        ALTER TABLE trips_businesstrip 
        ADD COLUMN IF NOT EXISTS senior_id BIGINT;
    """)

def reverse_migration(apps, schema_editor):
    # Откат (опционально)
    schema_editor.execute("DROP TABLE IF EXISTS trips_technicalstaffrecord;")
    # schema_editor.execute("ALTER TABLE trips_businesstrip DROP COLUMN IF EXISTS senior_id;")

class Migration(migrations.Migration):
    dependencies = [
        ('trips', '0002_technicalstaffrecord'),
    ]

    operations = [
        migrations.RunPython(create_missing_tables, reverse_migration),
    ] 