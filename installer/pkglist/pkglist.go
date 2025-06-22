package pkglist

var BrewPackges = []string{
	"colima",
	"terraform",
	"kubectl",
	"minio-mc",
	"kind",
	// "python@3.12",
	"go",
}

var DockerImages = []string{
	"postgres:15",
	"gitea/gitea:1.21.11",
	"gitea/act_runner:0.2.11",
	"apache/airflow:2.5.1-python3.9",
	"quay.io/argoproj/argocd:v2.10.7",
	"quay.io/minio/minio:RELEASE.2025-04-08T15-41-24Z",
	"python:3.12-slim",
	"public.ecr.aws/docker/library/redis:7.4.2-alpine",
	"registry:latest",
}
