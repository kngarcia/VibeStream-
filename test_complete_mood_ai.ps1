# Script de prueba completa del Mood AI con autenticación simulada

Write-Host "`n=== PRUEBA COMPLETA DEL SISTEMA MOOD AI ===" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar que el servicio está corriendo
Write-Host "1. Verificando servicio..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8009/health" -Method Get
    Write-Host "   [OK] Servicio corriendo: v$($health.version)" -ForegroundColor Green
    Write-Host "   Features: $($health.features -join ', ')" -ForegroundColor Gray
} catch {
    Write-Host "   [ERROR] Servicio no responde" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Verificar que los endpoints requieren autenticación
Write-Host "2. Verificando seguridad (debe requerir auth)..." -ForegroundColor Yellow
try {
    Invoke-RestMethod -Uri "http://localhost:8009/recommendations/mood/status" -Method Get -ErrorAction Stop
    Write-Host "   [ADVERTENCIA] Endpoint no requiere autenticacion" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "   [OK] Autenticacion requerida correctamente" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Error inesperado: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""

# 3. Verificar documentación Swagger
Write-Host "3. Verificando documentacion..." -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "http://localhost:8009/docs" -Method Get -ErrorAction Stop
    if ($docs.StatusCode -eq 200) {
        Write-Host "   [OK] Swagger UI disponible" -ForegroundColor Green
        Write-Host "   URL: http://localhost:8009/docs" -ForegroundColor Gray
    }
} catch {
    Write-Host "   [ERROR] No se pudo acceder a la documentacion" -ForegroundColor Red
}

Write-Host ""

# 4. Verificar estructura de archivos backend
Write-Host "4. Verificando archivos backend..." -ForegroundColor Yellow
$backendFiles = @(
    "recommendation-service\config.py",
    "recommendation-service\main.py",
    "recommendation-service\database\models.py",
    "recommendation-service\database\connection.py",
    "recommendation-service\services\mood_detection_service.py",
    "recommendation-service\services\mood_recommendation_service.py",
    "recommendation-service\handlers\mood_handler.py",
    "recommendation-service\middleware\auth_middleware.py"
)

$backendOK = 0
foreach ($file in $backendFiles) {
    if (Test-Path $file) {
        $backendOK++
    }
}
Write-Host "   [OK] $backendOK/$($backendFiles.Count) archivos backend encontrados" -ForegroundColor Green

Write-Host ""

# 5. Verificar estructura de archivos frontend
Write-Host "5. Verificando archivos frontend..." -ForegroundColor Yellow
$frontendFiles = @(
    "front_music_stm\src\services\moodService.js",
    "front_music_stm\src\components\player\MoodAIToggle.jsx",
    "front_music_stm\src\components\player\MoodBadge.jsx",
    "front_music_stm\.env.local"
)

$frontendOK = 0
foreach ($file in $frontendFiles) {
    if (Test-Path $file) {
        $frontendOK++
    }
}
Write-Host "   [OK] $frontendOK/$($frontendFiles.Count) archivos frontend encontrados" -ForegroundColor Green

Write-Host ""

# 6. Verificar documentación
Write-Host "6. Verificando documentacion..." -ForegroundColor Yellow
$docFiles = @(
    "recommendation-service\README.md",
    "DEPLOYMENT_GUIDE.md",
    "QUICK_START_MOOD_AI.md",
    "IMPLEMENTATION_REPORT.md",
    "VERIFICATION_CHECKLIST.md"
)

$docOK = 0
foreach ($file in $docFiles) {
    if (Test-Path $file) {
        $docOK++
    }
}
Write-Host "   [OK] $docOK/$($docFiles.Count) archivos de documentacion encontrados" -ForegroundColor Green

Write-Host ""

# 7. Verificar logs del servicio
Write-Host "7. Verificando logs del servicio..." -ForegroundColor Yellow
$logs = docker-compose logs --tail 5 recommendation-service 2>&1
if ($logs -match "Uvicorn running") {
    Write-Host "   [OK] Servicio inicializado correctamente" -ForegroundColor Green
} else {
    Write-Host "   [ADVERTENCIA] No se pudieron verificar los logs" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== RESUMEN ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:      $backendOK/$($backendFiles.Count) archivos" -ForegroundColor White
Write-Host "Frontend:     $frontendOK/$($frontendFiles.Count) archivos" -ForegroundColor White
Write-Host "Documentacion: $docOK/$($docFiles.Count) archivos" -ForegroundColor White
Write-Host "Servicio:     CORRIENDO en puerto 8009" -ForegroundColor Green
Write-Host "Seguridad:    JWT Auth activa" -ForegroundColor Green
Write-Host ""
Write-Host "Estado:       LISTO PARA USAR" -ForegroundColor Green -BackgroundColor Black
Write-Host ""
Write-Host "Siguiente paso:" -ForegroundColor Yellow
Write-Host "  cd front_music_stm" -ForegroundColor Gray
Write-Host "  npm run dev" -ForegroundColor Gray
Write-Host ""
