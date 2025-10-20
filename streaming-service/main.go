package main

import (
	"streaming-service/config"
	"streaming-service/database"
	"streaming-service/handlers"
	"streaming-service/middleware"
	"streaming-service/services"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/schema"
)

func main() {
	cfg := config.GetConfig()

	// Obtener conexión base (sql.DB del pool)
	sqlDB := database.GetDB()

	// Inicializar GORM una sola vez con el esquema "music_streaming"
	gormDB, err := gorm.Open(postgres.New(postgres.Config{
		Conn: sqlDB,
	}), &gorm.Config{
		NamingStrategy: schema.NamingStrategy{
			TablePrefix:   "music_streaming.",
			SingularTable: false,
		},
	})
	if err != nil {
		panic("❌ Error al inicializar GORM")
	}

	// Crear el servicio de canciones UNA sola vez
	songService := services.NewSongService(gormDB)

	r := gin.Default()

	// ✅ CONFIGURACIÓN CORS COMPLETA
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173", "http://localhost:3000", "https://mi-front-produccion.com"},
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Length", "Content-Type", "Authorization", "Range", "Accept-Ranges"},
		ExposeHeaders:    []string{"Content-Length", "Content-Range", "Accept-Ranges", "Content-Type"},
		AllowCredentials: true,
		MaxAge:           12 * 60 * 60, // 12 horas
	}))

	// Middleware de logs para debugging
	r.Use(func(c *gin.Context) {
		c.Next()
	})

	// Ruta de health check pública
	r.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{
			"status":  "ok",
			"service": "streaming",
			"port":    cfg.Port,
		})
	})

	// ✅ RUTA DE STREAMING PROTEGIDA CON MIDDLEWARE JWT
	// El middleware validará el token del header Authorization
	protected := r.Group("/")
	protected.Use(middleware.AuthMiddleware(cfg.JWTSecret))
	protected.GET("/stream", handlers.StreamSongHandler(songService))

	// Ruta pública para información de canciones
	r.GET("/song/:id/info", handlers.GetSongInfoHandler(songService))

	r.Run(":" + cfg.Port)
}