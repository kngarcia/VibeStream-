package main

import (
	"context"
	"history-service/config"
	"history-service/database"
	"history-service/events"
	"history-service/handlers"
	"history-service/middleware"
	"history-service/repositories"
	"history-service/services"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/gin-gonic/gin"
)

func main() {
	// Cargar configuración
	cfg := config.GetConfig()

	// Inicializar conexión a la base de datos
	db := database.GetDB()

	// Crear repositorio de historial
	historyRepo := repositories.NewHistoryRepository(db)

	// Crear servicio de historial
	historyService := services.NewHistoryService(historyRepo)

	// Crear handler
	historyHandler := handlers.NewHistoryHandler(historyService)

	// Gin router
	r := gin.Default()

	// Middleware de autenticación
	r.Use(middleware.AuthMiddleware(cfg.JWTSecret))

	// Rutas
	r.GET("/history", historyHandler.GetHistoryHandler)

	// Arrancar consumidor de eventos en segundo plano
	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		if err := events.StartConsumer(ctx, historyService); err != nil {
			log.Fatalf("❌ Error en consumidor de eventos: %v", err)
		}
	}()

	// Capturar señales para cierre graceful
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		if err := r.Run(":" + cfg.Port); err != nil {
			log.Fatalf("❌ Error arrancando servidor HTTP: %v", err)
		}
	}()

	log.Printf("✅ History service corriendo en puerto %s", cfg.Port)
	<-stop
	log.Println("⚡ Deteniendo servicio...")

	// Cancelar consumidor de eventos
	cancel()

	// Cerrar DB
	if err := db.Close(); err != nil {
		log.Println("❌ Error cerrando DB:", err)
	}

	log.Println("👋 Servicio detenido correctamente")
}
