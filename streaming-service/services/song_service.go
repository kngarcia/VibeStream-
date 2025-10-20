package services

import (
	"fmt"
	"os"
	"path/filepath"
	"streaming-service/models"
	"streaming-service/repositories"

	"gorm.io/gorm"
)

type SongService interface {
	GetSongURL(id uint) (string, error)
	GetSongInfo(id uint) (*models.Song, error) // Nuevo método
}

type songService struct {
	repo repositories.SongRepository
}

func NewSongService(db *gorm.DB) SongService {
	repo := repositories.NewSongRepository(db)
	return &songService{repo: repo}
}

func (s *songService) GetSongURL(id uint) (string, error) {
	relativePath, err := s.repo.GetSongURLByID(id)
	if err != nil {
		return "", err
	}

	basePath := os.Getenv("CONTENT_BASE_PATH")
	if basePath == "" {
		return "", fmt.Errorf("CONTENT_BASE_PATH no está definido en el entorno")
	}

	fullPath := filepath.Join(basePath, relativePath)
	return fullPath, nil
}

// Nuevo método para obtener información de la canción
func (s *songService) GetSongInfo(id uint) (*models.Song, error) {
	return s.repo.GetSongInfo(id)
}