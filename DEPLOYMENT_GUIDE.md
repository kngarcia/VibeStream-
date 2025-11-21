# 🚀 Guía de Despliegue - Modo Mood AI

## 📋 Pre-requisitos

- PostgreSQL corriendo (para migraciones)
- Docker y Docker Compose instalados
- Variables de entorno configuradas

## 🔧 Paso 1: Variables de Entorno

Agregar al archivo `.env` en la raíz del proyecto:

```env
# Agregar esta línea al archivo .env existente
RECOMMENDATION_PORT=8009
```

Verificar que ya existen estas variables:
```env
db_url_py=postgresql+asyncpg://usuario:contraseña@host:5432/database
JWT_SECRET=tu_secret_key
FRONTEND_ORIGINS=http://localhost:5173
CONTENT_BASE_PATH=/path/to/content
```

## 🗄️ Paso 2: Migraciones de Base de Datos

### Opción A: Manual con psql

```bash
# Conectarse a la base de datos
psql -h localhost -U tu_usuario -d tu_database

# Ejecutar migraciones en orden
\i recommendation-service/migrations/001_create_mood_tables.sql
\i recommendation-service/migrations/002_populate_initial_moods.sql

# Verificar tablas creadas
\dt music_streaming.track_mood_features
\dt music_streaming.user_mood_settings
\dt music_streaming.mood_session_context

# Verificar datos iniciales
SELECT primary_mood, COUNT(*) 
FROM music_streaming.track_mood_features 
GROUP BY primary_mood;
```

### Opción B: Script Python

```bash
cd recommendation-service

# Crear script temporal
cat > run_migrations.py << 'EOF'
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_migrations():
    # Parsear URL de conexión
    db_url = os.getenv('db_url_py')
    # Convertir de asyncpg a formato estándar
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    conn = await asyncpg.connect(db_url)
    
    print("🔄 Ejecutando migración 001...")
    with open('migrations/001_create_mood_tables.sql', 'r') as f:
        await conn.execute(f.read())
    print("✅ Migración 001 completada")
    
    print("🔄 Ejecutando migración 002...")
    with open('migrations/002_populate_initial_moods.sql', 'r') as f:
        await conn.execute(f.read())
    print("✅ Migración 002 completada")
    
    # Verificar
    count = await conn.fetchval('SELECT COUNT(*) FROM music_streaming.track_mood_features')
    print(f"\n📊 Total de canciones con mood: {count}")
    
    await conn.close()

if __name__ == '__main__':
    asyncio.run(run_migrations())
EOF

# Ejecutar
python run_migrations.py
```

## 🐳 Paso 3: Desplegar con Docker Compose

### Levantar solo el servicio nuevo

```bash
# Build de la imagen
docker-compose build recommendation-service

# Levantar el servicio
docker-compose up -d recommendation-service

# Ver logs
docker-compose logs -f recommendation-service
```

### Levantar todos los servicios

```bash
# Build y levantar todo
docker-compose up -d --build

# Verificar que todos los servicios están corriendo
docker-compose ps

# Deberías ver:
# - recommendation-service (puerto 8009)
# - auth-service
# - content-service
# - playlist-service
# - etc...
```

## ✅ Paso 4: Verificación

### 1. Health Check

```bash
curl http://localhost:8009/health
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "service": "recommendation-service",
  "version": "1.0.0",
  "features": ["mood_detection", "mood_recommendation"]
}
```

### 2. Verificar Base de Datos

```bash
# Conectarse al contenedor de PostgreSQL
docker exec -it <postgres_container> psql -U usuario -d database

# Verificar tablas
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'music_streaming' 
AND table_name LIKE '%mood%';

# Debería mostrar:
# - track_mood_features
# - user_mood_settings
# - mood_session_context
```

### 3. Probar API (requiere autenticación)

```bash
# Primero obtener un token
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tu_email@example.com","password":"tu_password"}' \
  | jq -r '.access_token')

# Verificar estado de Mood AI
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8009/recommendations/mood/status

# Activar Mood AI
curl -X POST http://localhost:8009/recommendations/mood/toggle \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled":true,"transition_smoothness":"medium"}'
```

## 🎨 Paso 5: Frontend

### 1. Configurar variable de entorno

Crear/editar `front_music_stm/.env`:

```env
VITE_RECOMMENDATION_SERVICE_URL=http://localhost:8009/recommendations
```

### 2. Instalar dependencias (si es necesario)

```bash
cd front_music_stm
npm install
```

### 3. Levantar frontend

```bash
npm run dev
```

### 4. Verificar integración

1. Abrir http://localhost:5173
2. Iniciar sesión
3. Ir al player (reproducir alguna canción)
4. Buscar el botón "✨ Mood AI" en el player
5. Hacer clic para activar
6. El botón debe cambiar de color y mostrar un emoji de mood

## 📊 Paso 6: Verificación Completa

### Checklist de Funcionalidad

- [ ] Servicio corriendo en puerto 8009
- [ ] Health check responde correctamente
- [ ] Tablas creadas en la base de datos
- [ ] Datos iniciales de mood poblados
- [ ] Frontend muestra el toggle de Mood AI
- [ ] Toggle se puede activar/desactivar
- [ ] Al activar, muestra el mood actual
- [ ] Las canciones tienen mood asignado

### Comandos de Diagnóstico

```bash
# Ver logs del servicio
docker-compose logs -f recommendation-service

# Ver estado de contenedores
docker-compose ps

# Ver uso de recursos
docker stats recommendation-service

# Conectarse al contenedor
docker exec -it recommendation-service bash

# Dentro del contenedor, verificar archivos
ls -la
cat config.py
```

## 🔧 Troubleshooting

### Problema: "Module not found"

```bash
# Reinstalar dependencias en el contenedor
docker-compose exec recommendation-service pip install -r requirements.txt
```

### Problema: "Connection refused" desde frontend

```bash
# Verificar CORS en config.py
# Asegurarse de que FRONTEND_ORIGINS incluye http://localhost:5173

# Reiniciar servicio
docker-compose restart recommendation-service
```

### Problema: "Table does not exist"

```bash
# Re-ejecutar migraciones
docker exec -it <postgres_container> psql -U usuario -d database -f /path/to/001_create_mood_tables.sql
```

### Problema: No hay canciones con mood

```bash
# Verificar que hay géneros en la BD
psql -c "SELECT COUNT(*) FROM music_streaming.genres;"

# Verificar que las canciones tienen género_id
psql -c "SELECT COUNT(*) FROM music_streaming.songs WHERE genre_id IS NOT NULL;"

# Re-ejecutar población de moods
psql -f recommendation-service/migrations/002_populate_initial_moods.sql
```

## 🔄 Actualización de Servicio

Si haces cambios al código:

```bash
# Reconstruir imagen
docker-compose build recommendation-service

# Reiniciar servicio
docker-compose up -d recommendation-service

# Ver logs en tiempo real
docker-compose logs -f recommendation-service
```

## 📈 Monitoreo

### Logs importantes a observar:

```bash
# Logs de arranque
docker-compose logs recommendation-service | grep "Application startup complete"

# Logs de requests
docker-compose logs recommendation-service | grep "POST /recommendations"

# Logs de errores
docker-compose logs recommendation-service | grep "ERROR"
```

### Métricas clave:

- **Tiempo de respuesta** de `/mood/next-track`: < 200ms
- **Tasa de error**: < 1%
- **Uso de memoria**: < 512MB
- **Uso de CPU**: < 50%

## 🎉 ¡Listo!

Si todos los pasos se completaron exitosamente, el Modo Mood AI está funcionando.

### Próximos Pasos:

1. **Testing**: Probar con diferentes géneros y playlists
2. **Ajustes**: Afinar compatibilidad de moods según feedback
3. **Fase 2**: Implementar análisis avanzado de audio
4. **Analytics**: Agregar métricas de uso del Mood AI

---

**¿Problemas?** Revisar los logs y la sección de Troubleshooting.

**¿Dudas?** Consultar `recommendation-service/README.md` o `MOOD_AI_INTEGRATION.md`.
