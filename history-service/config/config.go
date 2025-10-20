package config

import (
	"os"
	"sync"

	"github.com/joho/godotenv"
)

type Config struct {
	Port      string
	JWTSecret string
	DBURL     string
	RabbitURL string
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

		instance = &Config{
			Port:      getEnv("HISTORY_PORT", "8005"),
			JWTSecret: getEnv("JWT_SECRET", "defaultsecret"),
			DBURL:     getEnv("DB_URL", "postgres://user:pass@localhost:5432/dbname?sslmode=disable"),
			RabbitURL: getEnv("RABBITMQ_URL", "amqp://guest:guest@localhost/"),
		}
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
