package services

import (
	"streaming-service/models"
	"streaming-service/repositories"

	"gorm.io/gorm"
)

type SongService interface {
	GetSongURL(id uint) (string, error) // devuelve la S3 key
	GetSongInfo(id uint) (*models.Song, error)
}

type songService struct {
	repo repositories.SongRepository
}

func NewSongService(db *gorm.DB) SongService {
	repo := repositories.NewSongRepository(db)
	return &songService{repo: repo}
}

// Ahora esto ya NO arma rutas locales — devolvemos la KEY de S3
func (s *songService) GetSongURL(id uint) (string, error) {
	return s.repo.GetSongURLByID(id)
}

func (s *songService) GetSongInfo(id uint) (*models.Song, error) {
	return s.repo.GetSongInfo(id)
}
