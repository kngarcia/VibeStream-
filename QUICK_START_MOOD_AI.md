# 🚀 GUÍA RÁPIDA - MOOD AI

## ¿Qué es Mood AI?

Un sistema inteligente que mantiene la coherencia emocional en tu música. Cuando está activado, las canciones fluyen naturalmente manteniendo el mismo "mood" o estado de ánimo.

---

## 🎯 Inicio Rápido

### 1. Backend (Ya está corriendo ✅)

El servicio está funcionando en **http://localhost:8009**

Verifica:
```bash
curl http://localhost:8009/health
```

### 2. Frontend

```bash
cd front_music_stm
npm install
npm run dev
```

### 3. Usar la Funcionalidad

1. Abre http://localhost:5173
2. Inicia sesión
3. Ve al reproductor de música
4. Busca el botón "Mood AI" con icono de estrellitas ✨
5. Actívalo (se pondrá de color según el mood actual)
6. ¡Reproduce música y observa la coherencia!

---

## 🎵 Moods Disponibles

| Mood | Emoji | Géneros | Color |
|------|-------|---------|-------|
| **Chill** | 😌 | Lofi, Jazz, Ambient, Acoustic | Azul-Cyan |
| **Happy** | 😊 | Pop, Dance, Reggaeton | Amarillo-Naranja |
| **Sad** | 😢 | Blues, Ballad | Gris-Azul |
| **Energetic** | ⚡ | Rock, Electronic, Hip-Hop | Rosa-Rojo |
| **Intense** | 🔥 | Metal, Punk, Trap | Rojo-Púrpura |
| **Melancholic** | 🌙 | Indie, Folk, Soul | Índigo-Púrpura |

---

## 🎛️ Configuración

### Niveles de Transición

- **Strict** (0.3): Solo moods muy similares
  - Ejemplo: Chill → Chill, Happy → Energetic
  
- **Medium** (0.6): Transiciones suaves (por defecto)
  - Ejemplo: Chill → Happy, Sad → Melancholic
  
- **Flexible** (0.9): Casi cualquier transición
  - Ejemplo: Cualquier mood excepto extremos

### Cambiar Configuración

```javascript
// En el frontend, el toggle usa 'medium' por defecto
// Para cambiar, edita MoodAIToggle.jsx
```

---

## 📡 API Endpoints

### Activar/Desactivar Mood AI
```bash
POST http://localhost:8009/recommendations/mood/toggle
Headers: Authorization: Bearer YOUR_JWT_TOKEN
Body: {
  "enabled": true,
  "transition_smoothness": "medium"
}
```

### Obtener Estado
```bash
GET http://localhost:8009/recommendations/mood/status
Headers: Authorization: Bearer YOUR_JWT_TOKEN
```

### Siguiente Canción
```bash
POST http://localhost:8009/recommendations/mood/next-track
Headers: Authorization: Bearer YOUR_JWT_TOKEN
Body: {
  "context_type": "explore",
  "context_id": null
}
```

### Registrar Skip
```bash
POST http://localhost:8009/recommendations/mood/skip
Headers: Authorization: Bearer YOUR_JWT_TOKEN
Body: {
  "track_id": 123
}
```

---

## 🔧 Comandos Útiles

### Ver Logs
```bash
docker-compose logs -f recommendation-service
```

### Reiniciar Servicio
```bash
docker-compose restart recommendation-service
```

### Reconstruir
```bash
docker-compose build recommendation-service
docker-compose up -d recommendation-service
```

### Ver Estado
```bash
docker-compose ps recommendation-service
```

---

## 🐛 Troubleshooting

### El servicio no inicia
```bash
# Ver logs completos
docker-compose logs recommendation-service

# Verificar que el puerto 8009 esté libre
netstat -an | findstr "8009"

# Reconstruir e iniciar
docker-compose down recommendation-service
docker-compose build recommendation-service
docker-compose up -d recommendation-service
```

### No se detectan moods
```bash
# Verificar que las tablas existen
docker exec -it <postgres-container> psql -U usuario -d database -c "\dt music_streaming.*"

# Las tablas se crean automáticamente al iniciar el servicio
```

### Frontend no conecta
```bash
# Verificar variable de entorno
cat front_music_stm/.env.local

# Debe tener:
# VITE_RECOMMENDATION_SERVICE_URL=http://localhost:8009/recommendations

# Reiniciar frontend
cd front_music_stm
npm run dev
```

### Error de CORS
```bash
# Verificar FRONTEND_ORIGINS en .env
cat .env | grep FRONTEND_ORIGINS

# Debe incluir:
# FRONTEND_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## 📊 Monitoreo

### Health Check
```bash
curl http://localhost:8009/health
```

Respuesta esperada:
```json
{
  "status": "ok",
  "service": "recommendation-service",
  "version": "1.0.0",
  "features": ["mood_detection", "mood_recommendation"]
}
```

### Documentación Interactiva
Abre en tu navegador:
```
http://localhost:8009/docs
```

---

## 💡 Tips

1. **Primera Reproducción**: La primera canción siempre es aleatoria. Después de 1-2 canciones, el algoritmo aprende tu mood.

2. **Skips**: Si haces skip, el sistema lo registra y ajusta el mood dominante.

3. **Playlists Pequeñas**: Si tienes pocas canciones, el sistema automáticamente relaja las restricciones.

4. **Cambio de Mood**: Para cambiar el mood, reproduce manualmente una canción de otro género.

---

## 🎓 Ejemplos de Uso

### Escenario 1: Sesión de Estudio
1. Activa Mood AI
2. Reproduce una canción lofi
3. El sistema mantendrá: Chill → Chill → Ambient → Jazz

### Escenario 2: Entrenamiento
1. Activa Mood AI
2. Reproduce una canción de rock
3. El sistema mantendrá: Energetic → Electronic → Hip-Hop → Rock

### Escenario 3: Noche Tranquila
1. Activa Mood AI
2. Reproduce una canción indie
3. El sistema mantendrá: Melancholic → Folk → Soul → Indie

---

## 📞 Ayuda Adicional

- 📖 Documentación completa: `README.md`
- 🚀 Guía de despliegue: `DEPLOYMENT_GUIDE.md`
- 📊 Resumen del proyecto: `MOOD_AI_PROJECT_SUMMARY.md`
- ✅ Reporte de implementación: `IMPLEMENTATION_REPORT.md`

---

**¡Disfruta de tu música con coherencia emocional! 🎵✨**
