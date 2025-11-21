# Mood AI Migration Scripts

Este directorio contiene los scripts de migración necesarios para la funcionalidad **Modo Mood AI**.

## Orden de ejecución

1. **001_create_mood_tables.sql** - Crea las tablas necesarias
2. **002_populate_initial_moods.sql** - Popula datos iniciales de mood para canciones existentes

## Cómo ejecutar

### Opción 1: Usando psql
```bash
psql -h localhost -U your_user -d your_database -f migrations/001_create_mood_tables.sql
psql -h localhost -U your_user -d your_database -f migrations/002_populate_initial_moods.sql
```

### Opción 2: Usando script Python
```bash
cd recommendation-service
python migrations/run_migrations.py
```

### Opción 3: Automático en Docker
Las migraciones se ejecutarán automáticamente al iniciar el servicio si configuramos un init script.

## Tablas creadas

- **track_mood_features**: Características de mood de cada canción
- **user_mood_settings**: Configuración del usuario para Mood AI
- **mood_session_context**: Contexto de sesión de reproducción con mood

## Notas

- Las migraciones son idempotentes (pueden ejecutarse múltiples veces sin problemas)
- Se usan `IF NOT EXISTS` y `ON CONFLICT` para evitar duplicados
- Los datos iniciales se basan en el género de la canción
