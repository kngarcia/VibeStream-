package utils

import (
	"fmt"
	"streaming-service/config"
	"strings"
)

// ExtractS3KeyFromURL extrae la key de S3 desde una URL completa
// Soporta tanto AWS real como LocalStack
func ExtractS3KeyFromURL(url string) (string, error) {
	cfg := config.GetConfig()

	// Para LocalStack: http://localhost:4566/bucket/key
	if cfg.AWSEndpointURL != "" && strings.HasPrefix(url, cfg.AWSEndpointURL) {
		prefix := fmt.Sprintf("%s/%s/", cfg.AWSEndpointURL, cfg.AWSS3Bucket)
		if strings.HasPrefix(url, prefix) {
			return strings.TrimPrefix(url, prefix), nil
		}
	}

	// Para AWS real: https://bucket.s3.region.amazonaws.com/key
	prefix := fmt.Sprintf("https://%s.s3.%s.amazonaws.com/", cfg.AWSS3Bucket, cfg.AWSRegion)
	if strings.HasPrefix(url, prefix) {
		return strings.TrimPrefix(url, prefix), nil
	}

	// Si no coincide con ningún patrón, retornar error
	return "", fmt.Errorf("no se pudo extraer la key de la URL: %s", url)
}
