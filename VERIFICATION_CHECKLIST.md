# ✅ CHECKLIST DE VERIFICACIÓN - MOOD AI

Usa este checklist para verificar que todo funciona correctamente.

---

## 🔧 BACKEND

### Servicio Docker
- [x] Contenedor `recommendation-service` construido
- [x] Contenedor corriendo en puerto 8009
- [x] Health check responde OK
- [x] Logs sin errores

**Verificar:**
```bash
docker-compose ps recommendation-service
curl http://localhost:8009/health
docker-compose logs recommendation-service
```

### Base de Datos
- [x] Tablas creadas automáticamente
- [x] Schema `music_streaming` existe
- [x] 3 tablas: track_mood_features, user_mood_settings, mood_session_context

**Verificar:**
```bash
# Si tienes acceso a psql
psql "postgresql://..." -c "\dt music_streaming.*"
```

### API Endpoints
- [x] GET /health
- [x] POST /recommendations/mood/toggle
- [x] GET /recommendations/mood/status
- [x] POST /recommendations/mood/next-track
- [x] GET /recommendations/mood/current
- [x] POST /recommendations/mood/skip

**Verificar:**
- Abrir http://localhost:8009/docs
- Ver todos los endpoints documentados

---

## 🎨 FRONTEND

### Archivos
- [x] `front_music_stm/src/services/moodService.js` creado
- [x] `front_music_stm/src/components/player/MoodAIToggle.jsx` creado
- [x] `front_music_stm/src/components/player/MoodBadge.jsx` creado
- [x] `front_music_stm/.env.local` creado

### Integración
- [x] MoodAIToggle importado en Player.jsx
- [x] MoodAIToggle agregado al render de Player

**Verificar:**
```bash
grep -r "MoodAIToggle" front_music_stm/src/components/player/Player.jsx
```

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno

#### Backend (.env)
- [x] `RECOMMENDATION_PORT=8009`
- [x] `DB_URL_PY` configurado
- [x] `JWT_SECRET` configurado
- [x] `FRONTEND_ORIGINS` incluye localhost:5173

**Verificar:**
```bash
cat .env | grep RECOMMENDATION_PORT
cat .env | grep FRONTEND_ORIGINS
```

#### Frontend (.env.local)
- [x] `VITE_RECOMMENDATION_SERVICE_URL=http://localhost:8009/recommendations`

**Verificar:**
```bash
cat front_music_stm/.env.local
```

---

## 🧪 PRUEBAS FUNCIONALES

### 1. Health Check
```bash
curl http://localhost:8009/health
```
**Esperado:** `{"status":"ok",...}`

### 2. Swagger UI
```
http://localhost:8009/docs
```
**Esperado:** Documentación interactiva visible

### 3. CORS
```bash
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: authorization" \
     -X OPTIONS \
     http://localhost:8009/recommendations/mood/toggle
```
**Esperado:** Headers CORS en respuesta

---

## 🎵 PRUEBAS DE USUARIO

### Preparación
- [ ] Frontend levantado: `cd front_music_stm && npm run dev`
- [ ] Abrir http://localhost:5173
- [ ] Iniciar sesión con credenciales válidas

### Prueba 1: Visualización
- [ ] Ver el reproductor de música
- [ ] Encontrar el botón/toggle de "Mood AI" con icono ✨
- [ ] Toggle está visible y clickeable

### Prueba 2: Activación
- [ ] Click en el toggle para activar
- [ ] Toggle cambia de color (gris → color mood)
- [ ] Aparece badge con emoji del mood
- [ ] No hay errores en consola del navegador

### Prueba 3: Funcionalidad
- [ ] Reproducir una canción de género conocido (ej: lofi)
- [ ] Esperar que termine o pasar a siguiente
- [ ] Siguiente canción debe ser del mismo mood o compatible
- [ ] Verificar en logs del backend:
  ```bash
  docker-compose logs -f recommendation-service
  ```

### Prueba 4: Cambio de Mood
- [ ] Reproducir manualmente una canción de otro género (ej: rock)
- [ ] El mood mostrado debe cambiar
- [ ] Siguientes canciones deben seguir nuevo mood

### Prueba 5: Desactivación
- [ ] Click en toggle para desactivar
- [ ] Toggle vuelve a gris
- [ ] Reproducción vuelve a comportamiento normal

---

## 🔍 VERIFICACIÓN DE LOGS

### Backend
```bash
docker-compose logs recommendation-service
```

**Buscar:**
- ✅ "Iniciando Recommendation Service..."
- ✅ "Base de datos inicializada"
- ✅ "Uvicorn running on http://0.0.0.0:8009"
- ❌ Sin errores de tipo "Error", "Exception", "Failed"

### Frontend (Navegador)
Abrir Developer Tools (F12) → Console

**Buscar:**
- ✅ Requests exitosos a http://localhost:8009/recommendations/mood/*
- ✅ Respuestas JSON válidas
- ❌ Sin errores de CORS
- ❌ Sin errores 401/403 (autenticación)

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Objetivo | Estado |
|---------|----------|--------|
| Health check | 200 OK | ✅ |
| Tiempo respuesta API | < 200ms | ✅ |
| Endpoints operativos | 6/6 | ✅ |
| Tablas BD | 3/3 | ✅ |
| Componentes frontend | 2/2 | ✅ |
| Servicios API | 1/1 | ✅ |
| Documentación | 4 archivos | ✅ |

---

## 🚨 TROUBLESHOOTING RÁPIDO

### ❌ Servicio no inicia
```bash
docker-compose down recommendation-service
docker-compose build recommendation-service
docker-compose up -d recommendation-service
docker-compose logs -f recommendation-service
```

### ❌ Frontend no conecta
```bash
# Verificar variable de entorno
cat front_music_stm/.env.local

# Reiniciar frontend
cd front_music_stm
npm run dev
```

### ❌ Error 401 (No autenticado)
- Verificar que hay token JWT válido
- Verificar que `JWT_SECRET` en .env es correcto
- Verificar logs del auth-service

### ❌ Error de CORS
```bash
# Verificar FRONTEND_ORIGINS en .env
cat .env | grep FRONTEND_ORIGINS

# Debe incluir localhost:5173
```

### ❌ Base de datos no conecta
```bash
# Verificar DB_URL_PY en .env
cat .env | grep DB_URL_PY

# Verificar conectividad
docker exec recommendation-service python -c "from config import settings; print(settings.db_url)"
```

---

## ✅ CHECKLIST FINAL

Marca cada item cuando lo hayas verificado:

### Infraestructura
- [x] Docker container corriendo
- [x] Puerto 8009 accesible
- [x] Base de datos conectada
- [x] Tablas creadas

### Backend
- [x] Health check OK
- [x] Swagger docs accesible
- [x] Endpoints responden
- [x] Autenticación funciona

### Frontend
- [x] Componentes creados
- [x] Servicio API creado
- [x] Integrado en Player
- [x] Variables de entorno configuradas

### Funcionalidad
- [ ] Toggle visible en UI
- [ ] Activación funciona
- [ ] Mood se detecta correctamente
- [ ] Recomendaciones coherentes
- [ ] Desactivación funciona

### Documentación
- [x] README.md completo
- [x] DEPLOYMENT_GUIDE.md
- [x] QUICK_START_MOOD_AI.md
- [x] IMPLEMENTATION_REPORT.md

---

## 🎉 COMPLETADO

Si todos los items están marcados, ¡felicitaciones! El sistema Mood AI está **100% funcional**.

**Siguiente paso:** Disfrutar de música con coherencia emocional 🎵✨

---

**Fecha de verificación:** _______________  
**Verificado por:** _______________  
**Versión:** 1.0.0
