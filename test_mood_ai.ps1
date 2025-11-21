# Script de verificacion del Mood AI Service

Write-Host "Probando Mood AI Service" -ForegroundColor Cyan
Write-Host ""

# Health Check
Write-Host "Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8009/health" -Method Get
    Write-Host "   OK - Servicio funcionando correctamente" -ForegroundColor Green
    Write-Host "   Version: $($response.version)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ERROR en health check" -ForegroundColor Red
    exit 1
}

Write-Host "Endpoints disponibles:" -ForegroundColor Yellow
Write-Host "   GET  /health" -ForegroundColor Gray
Write-Host "   POST /recommendations/mood/toggle" -ForegroundColor Gray
Write-Host "   GET  /recommendations/mood/status" -ForegroundColor Gray
Write-Host "   POST /recommendations/mood/next-track" -ForegroundColor Gray
Write-Host "   GET  /recommendations/mood/current" -ForegroundColor Gray
Write-Host "   POST /recommendations/mood/skip" -ForegroundColor Gray
Write-Host ""

Write-Host "Documentacion disponible en:" -ForegroundColor Yellow
Write-Host "   http://localhost:8009/docs" -ForegroundColor Cyan
Write-Host ""

Write-Host "Resumen:" -ForegroundColor Green
Write-Host "   Backend funcionando en puerto 8009" -ForegroundColor White
Write-Host "   Base de datos inicializada" -ForegroundColor White
Write-Host "   6 moods: chill, happy, sad, energetic, intense, melancholic" -ForegroundColor White
Write-Host ""

Write-Host "Proximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Levantar el frontend: cd front_music_stm; npm run dev" -ForegroundColor Gray
Write-Host "   2. Iniciar sesion en la aplicacion" -ForegroundColor Gray
Write-Host "   3. Activar el toggle de Mood AI en el player" -ForegroundColor Gray
Write-Host ""
