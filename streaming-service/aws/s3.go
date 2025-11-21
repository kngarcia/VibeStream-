package aws

import (
	"context"
	"streaming-service/config"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	s3 "github.com/aws/aws-sdk-go-v2/service/s3"
)

var (
	S3     *s3.Client
	Bucket string
)

func InitS3() error {
	cfg := config.GetConfig()

	var awsCfg aws.Config
	var err error

	// Si tenemos credenciales explícitas, usarlas
	if cfg.AWSAccessKeyID != "" && cfg.AWSSecretAccessKey != "" {
		var creds aws.CredentialsProvider
		if cfg.AWSSessionToken != "" {
			// Con session token (cuentas educativas/temporales)
			creds = aws.NewCredentialsCache(credentials.NewStaticCredentialsProvider(
				cfg.AWSAccessKeyID,
				cfg.AWSSecretAccessKey,
				cfg.AWSSessionToken,
			))
		} else {
			// Sin session token (cuentas IAM permanentes)
			creds = aws.NewCredentialsCache(credentials.NewStaticCredentialsProvider(
				cfg.AWSAccessKeyID,
				cfg.AWSSecretAccessKey,
				"", // Sin session token
			))
		}

		awsCfg, err = awsconfig.LoadDefaultConfig(
			context.TODO(),
			awsconfig.WithRegion(cfg.AWSRegion),
			awsconfig.WithCredentialsProvider(creds),
		)
	} else {
		// Usar credenciales por defecto (perfil AWS, IAM role, etc.)
		awsCfg, err = awsconfig.LoadDefaultConfig(
			context.TODO(),
			awsconfig.WithRegion(cfg.AWSRegion),
		)
	}
	if err != nil {
		return err
	}

	// Configurar opciones para el cliente S3
	var s3Options []func(*s3.Options)

	// Si hay un endpoint personalizado (LocalStack), usarlo
	if cfg.AWSEndpointURL != "" {
		s3Options = append(s3Options, func(o *s3.Options) {
			o.BaseEndpoint = &cfg.AWSEndpointURL
			o.UsePathStyle = true // LocalStack requiere path-style
		})
		println("🔧 Usando endpoint personalizado:", cfg.AWSEndpointURL)
	}

	S3 = s3.NewFromConfig(awsCfg, s3Options...)
	Bucket = cfg.AWSS3Bucket

	println("☁️  S3 client inicializado")
	return nil
}
