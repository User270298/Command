from django.db import migrations

def fix_technical_staff_table(apps, schema_editor):
    # Добавляем недостающие столбцы в существующую таблицу trips_technicalstaffrecord
    schema_editor.execute("""
        ALTER TABLE trips_technicalstaffrecord 
        ADD COLUMN IF NOT EXISTS week DATE,
        ADD COLUMN IF NOT EXISTS value INTEGER,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS organization_id BIGINT,
        ADD COLUMN IF NOT EXISTS user_id BIGINT;
    """)
    
    # Добавляем внешние ключи (без IF NOT EXISTS)
    try:
        schema_editor.execute("""
            ALTER TABLE trips_technicalstaffrecord 
            ADD CONSTRAINT fk_technical_staff_organization 
            FOREIGN KEY (organization_id) REFERENCES trips_organization(id);
        """)
    except:
        pass  # Ограничение уже существует
    
    try:
        schema_editor.execute("""
            ALTER TABLE trips_technicalstaffrecord 
            ADD CONSTRAINT fk_technical_staff_user 
            FOREIGN KEY (user_id) REFERENCES users_user(id);
        """)
    except:
        pass  # Ограничение уже существует
    
    # Если таблица trips_organization_fixed_records существует, удаляем её
    schema_editor.execute("""
        DROP TABLE IF EXISTS trips_organization_fixed_records;
    """)

def reverse_migration(apps, schema_editor):
    # Откат (опционально)
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('trips', '0003_fix_missing_tables'),
    ]

    operations = [
        migrations.RunPython(fix_technical_staff_table, reverse_migration),
    ] 