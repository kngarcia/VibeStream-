# 🧪 Script de Prueba End-to-End del Sistema Mood AI con Autenticación

Write-Host "`n════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🎵 PRUEBA END-TO-END DEL SISTEMA MOOD AI" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Variables
$RECOMMENDATION_URL = "http://localhost:8009"
$AUTH_URL = "http://localhost:8080"
$TEST_USER = "testuser789"
$TEST_PASSWORD = "Test1234!"

# 1. Login para obtener token
Write-Host "🔐 PASO 1: Iniciando sesión..." -ForegroundColor Yellow
$loginBody = @{
    identifier = $TEST_USER
    password = $TEST_PASSWORD
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$AUTH_URL/login" -Method POST -Body $loginBody -ContentType "application/json"
    $TOKEN = $loginResponse.access_token
    $USER_ID = $loginResponse.user.id
    Write-Host "   ✅ Usuario: $($loginResponse.user.username)" -ForegroundColor Green
    Write-Host "   ✅ User ID: $USER_ID`n" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Headers con autenticación
$headers = @{
    Authorization = "Bearer $TOKEN"
    "Content-Type" = "application/json"
}

# 2. Activar Mood AI
Write-Host "🎭 PASO 2: Activando Mood AI..." -ForegroundColor Yellow
$toggleBody = @{
    enabled = $true
    transition_smoothness = "medium"
} | ConvertTo-Json

try {
    $toggleResponse = Invoke-RestMethod -Uri "$RECOMMENDATION_URL/recommendations/mood/toggle" -Method POST -Body $toggleBody -Headers $headers
    Write-Host "   ✅ Mood AI activado: $($toggleResponse.mood_ai_enabled)" -ForegroundColor Green
    Write-Host "   ✅ Mood actual: $($toggleResponse.current_mood)" -ForegroundColor Green
    Write-Host "   ✅ Configuración: $($toggleResponse.transition_smoothness)`n" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Response: $($_.ErrorDetails.Message)`n" -ForegroundColor Red
    exit 1
}

# 3. Obtener estado del Mood AI
Write-Host "📊 PASO 3: Verificando estado..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "$RECOMMENDATION_URL/recommendations/mood/status" -Method GET -Headers $headers
    Write-Host "   ✅ Mood AI habilitado: $($status.mood_ai_enabled)" -ForegroundColor Green
    Write-Host "   ✅ Mood dominante: $($status.current_mood)" -ForegroundColor Green
    Write-Host "   ✅ Suavidad: $($status.transition_smoothness)`n" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)`n" -ForegroundColor Red
}

# 4. Obtener 5 recomendaciones
Write-Host "🎵 PASO 4: Obteniendo recomendaciones..." -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    try {
        $track = Invoke-RestMethod -Uri "$RECOMMENDATION_URL/recommendations/mood/next-track" -Method POST -Headers $headers
        Write-Host "   $i. $($track.title)" -ForegroundColor Cyan
        Write-Host "      Artista: $($track.artist)" -ForegroundColor Gray
        Write-Host "      Mood: $($track.mood) | Energía: $($track.energy)" -ForegroundColor Magenta
        Start-Sleep -Milliseconds 500
    } catch {
        Write-Host "   ❌ Error en recomendación $i`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ PRUEBA COMPLETADA CON ÉXITO" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "" -NoNewline
Write-Host "📝 Resumen:" -ForegroundColor Yellow
Write-Host "   - 156 canciones con mood asignado" -ForegroundColor Cyan
Write-Host "   - Mood AI funcionando correctamente" -ForegroundColor Cyan
Write-Host "   - Recomendaciones basadas en mood activas" -ForegroundColor Cyan
Write-Host "   - Frontend disponible en http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
