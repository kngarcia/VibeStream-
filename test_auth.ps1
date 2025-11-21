# Script de prueba para autenticación

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  TEST DE AUTENTICACION" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan

# Generar un timestamp único para el usuario
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$username = "user$timestamp"
$email = "$username@test.com"
$password = "Test1234!"

Write-Host "1. REGISTRO DE USUARIO" -ForegroundColor Yellow
Write-Host "   Username: $username" -ForegroundColor Gray
Write-Host "   Email: $email" -ForegroundColor Gray

$registerBody = @{
    username = $username
    email = $email
    password = $password
    birthdate = "1995-05-15"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod -Uri 'http://localhost:8080/register' -Method Post -Body $registerBody -ContentType 'application/json'
    Write-Host "   ✅ Usuario registrado exitosamente" -ForegroundColor Green
    Write-Host "   ID: $($registerResponse.user.id)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Error en registro: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 1

Write-Host "`n2. LOGIN" -ForegroundColor Yellow
Write-Host "   Email: $email" -ForegroundColor Gray

$loginBody = @{
    identifier = $email
    password = $password
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri 'http://localhost:8080/login' -Method Post -Body $loginBody -ContentType 'application/json'
    Write-Host "   ✅ Login exitoso" -ForegroundColor Green
    Write-Host "   Access Token: $($loginResponse.access_token.Substring(0,30))..." -ForegroundColor Gray
    Write-Host "   Usuario: $($loginResponse.user.username)" -ForegroundColor Gray
    $accessToken = $loginResponse.access_token
} catch {
    Write-Host "   ❌ Error en login: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 1

Write-Host "`n3. OBTENER PERFIL" -ForegroundColor Yellow

try {
    $headers = @{
        'Authorization' = "Bearer $accessToken"
        'Content-Type' = 'application/json'
    }
    $profileResponse = Invoke-RestMethod -Uri 'http://localhost:8080/user/me' -Method Get -Headers $headers
    Write-Host "   ✅ Perfil obtenido exitosamente" -ForegroundColor Green
    Write-Host "   ID: $($profileResponse.id)" -ForegroundColor Gray
    Write-Host "   Username: $($profileResponse.username)" -ForegroundColor Gray
    Write-Host "   Email: $($profileResponse.email)" -ForegroundColor Gray
    Write-Host "   Role: $($profileResponse.role)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Error al obtener perfil: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ✅ TODAS LAS PRUEBAS EXITOSAS" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Puedes usar estas credenciales para probar en el navegador:" -ForegroundColor Yellow
Write-Host "  Email: $email" -ForegroundColor White
Write-Host "  Password: $password" -ForegroundColor White
Write-Host "`nAbre: http://localhost:5173`n" -ForegroundColor Cyan
