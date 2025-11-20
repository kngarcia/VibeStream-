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

	creds := aws.NewCredentialsCache(credentials.NewStaticCredentialsProvider(
		cfg.AWSAccessKeyID,
		cfg.AWSSecretAccessKey,
		cfg.AWSSessionToken,
	))

	awsCfg, err := awsconfig.LoadDefaultConfig(
		context.TODO(),
		awsconfig.WithRegion(cfg.AWSRegion),
		awsconfig.WithCredentialsProvider(creds),
	)
	if err != nil {
		return err
	}

	S3 = s3.NewFromConfig(awsCfg)
	Bucket = cfg.AWSS3Bucket

	println("☁️  S3 client inicializado")
	return nil
}
