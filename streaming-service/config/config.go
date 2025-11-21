package config

import (
	"os"
	"strings"
	"sync"

	"github.com/joho/godotenv"
)

type Config struct {
	Port            string
	JWTSecret       string
	DBURL           string
	RabbitURL       string
	AllowedOrigins  []string // Nuevo campo para CORS
}

var (
	instance *Config
	once     sync.Once
)

// GetConfig devuelve la instancia singleton de Config
func GetConfig() *Config {
	once.Do(func() {
		// Cargar .env solo si existe
		_ = godotenv.Load()

		// Obtener origins del environment o usar defaults
		origins := getEnv("FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:3000,http://localhost:5174")
		allowedOrigins := strings.Split(origins, ",")
		
		instance = &Config{
			Port:           getEnv("STREAMING_PORT", "8001"),
			JWTSecret:      getEnv("JWT_SECRET", "defaultsecret"),
			DBURL:          getEnv("DB_URL", "postgres://user:pass@localhost:5432/dbname?sslmode=disable"),
			RabbitURL:      getEnv("RABBITMQ_URL", "amqp://guest:guest@localhost/"),
			AllowedOrigins: allowedOrigins,
		}

		// Log de configuración (sin secret)
		println("🔧 Streaming Service Config:")
		println("   Port:", instance.Port)
		println("   Allowed Origins:", strings.Join(instance.AllowedOrigins, ", "))
		println("   DB URL:", maskDBURL(instance.DBURL))
	})
	return instance
}

// getEnv devuelve la variable de entorno o un valor por defecto
func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

// maskDBURL enmascara la contraseña en la URL de la base de datos para logs
func maskDBURL(dbURL string) string {
	parts := strings.Split(dbURL, "@")
	if len(parts) > 1 {
		return "***@" + parts[1]
	}
	return "***"
}