package repositories

import (
	"streaming-service/models"

	"gorm.io/gorm"
)

type SongRepository interface {
	GetSongURLByID(id uint) (string, error)
	GetSongInfo(id uint) (*models.Song, error) // Nuevo método
}

type songRepository struct {
	db *gorm.DB
}

func NewSongRepository(db *gorm.DB) SongRepository {
	return &songRepository{db: db}
}

func (r *songRepository) GetSongURLByID(id uint) (string, error) {
	var song models.Song
	err := r.db.Select("audio_url").First(&song, id).Error
	if err != nil {
		return "", err
	}
	return song.AudioURL, nil
}

// método para obtener información completa de la canción
func (r *songRepository) GetSongInfo(id uint) (*models.Song, error) {
	var song models.Song
	err := r.db.
		Preload("Album").
		Preload("Genre").
		Preload("Artists").
		First(&song, id).Error
	if err != nil {
		return nil, err
	}
	return &song, nil
}