module "kind_cluster" {
  source = "./iac"
}

resource "null_resource" "kind_cluster_resource" {
  provisioner "local-exec" {
    command = <<-EOT
      until docker ps -a --format '{{.Names}}' | grep -q '^local-cluster-control-plane$'; do
        echo "Waiting for kind node container..."
        sleep 2
      done

      docker update --cpus=2 --memory=2g --memory-swap=2g local-cluster-worker && \
      docker update --cpus=2 --memory=4g --memory-swap=4g local-cluster-worker2 && \
      docker update --cpus=2 --memory=2g --memory-swap=2g local-cluster-worker3 && \
      docker update --cpus=2 --memory=4g --memory-swap=4g local-cluster-worker4 && \
      docker restart local-cluster-worker local-cluster-worker2 local-cluster-worker3 local-cluster-worker4

    EOT
  }
  depends_on = [module.kind_cluster]
}

resource "null_resource" "image_load" {
  provisioner "local-exec" {
    command = <<-EOT
    docker start registry.local
    docker tag custom-airflow:0.1 localhost:5000/custom-airflow:0.1
    docker push localhost:5000/custom-airflow:0.1
    docker tag k8s.gcr.io/git-sync/git-sync:v3.6.6 localhost:5000/k8s.gcr.io/git-sync/git-sync:v3.6.6
    docker push localhost:5000/k8s.gcr.io/git-sync/git-sync:v3.6.6
    docker tag quay.io/argoproj/argocd:v2.14.10 localhost:5000/quay.io/argoproj/argocd:v2.14.10
    docker push localhost:5000/quay.io/argoproj/argocd:v2.14.10
    docker tag public.ecr.aws/docker/library/redis:7.4.2-alpine localhost:5000/public.ecr.aws/docker/library/redis:7.4.2-alpine
    docker push localhost:5000/public.ecr.aws/docker/library/redis:7.4.2-alpine
    docker tag ghcr.io/dexidp/dex:v2.42.1 localhost:5000/ghcr.io/dexidp/dex:v2.42.1
    docker push localhost:5000/ghcr.io/dexidp/dex:v2.42.1
    docker tag quay.io/argoproj/argocd:v2.10.7 localhost:5000/quay.io/argoproj/argocd:v2.10.7
    docker push localhost:5000/quay.io/argoproj/argocd:v2.10.7
    docker tag k8s.gcr.io/git-sync/git-sync:v3.6.6 localhost:5000/k8s.gcr.io/git-sync/git-sync:v3.6.6
    docker push localhost:5000/k8s.gcr.io/git-sync/git-sync:v3.6.6
    docker tag gitea/act_runner:0.2.11 localhost:5000/gitea/act_runner:0.2.11
    docker push localhost:5000/gitea/act_runner:0.2.11
    docker tag docker:dind localhost:5000/docker:dind
    docker push localhost:5000/docker:dind
    docker tag public.ecr.aws/docker/library/redis:7.4.2-alpine localhost:5000/public.ecr.aws/docker/library/redis:7.4.2-alpine
    docker push localhost:5000/public.ecr.aws/docker/library/redis:7.4.2-alpine
    docker tag public.ecr.aws/docker/library/redis:7.4.2-alpine localhost:5000/public.ecr.aws/docker/library/redis:7.4.2-alpine
    docker push localhost:5000/public.ecr.aws/docker/library/redis:7.4.2-alpine
    docker tag ubuntu:latest localhost:5000/ubuntu:latest
    docker push localhost:5000/ubuntu:latest
    docker push localhost:5000/custom-python:3.12-slim
    docker tag postgres:15 localhost:5000/postgres:15
    docker push localhost:5000/postgres:15
    docker tag gitea/gitea:1.21.11 localhost:5000/gitea/gitea:1.21.11
    docker push localhost:5000/gitea/gitea:1.21.11
    docker tag registry.k8s.io/ingress-nginx/controller:v1.9.4 localhost:5000/registry.k8s.io/ingress-nginx/controller:v1.9.4
    docker push localhost:5000/registry.k8s.io/ingress-nginx/controller:v1.9.4
    docker tag quay.io/minio/minio:RELEASE.2025-04-08T15-41-24Z localhost:5000/quay.io/minio/minio:RELEASE.2025-04-08T15-41-24Z
    docker push localhost:5000/quay.io/minio/minio:RELEASE.2025-04-08T15-41-24Z

  EOT
  }
  depends_on = [null_resource.kind_cluster_resource]
}

module "application" {
  source = "./modules/application"
  kubeconfig = module.kind_cluster.kubeconfig_path
  ansible_python_interpreter = module.kind_cluster.ansible_python_interpreter
  depends_on = [null_resource.image_load]
}

module "nginx" {
  source = "./modules/nginx"
  kubeconfig = module.kind_cluster.kubeconfig_path
  ansible_python_interpreter = module.kind_cluster.ansible_python_interpreter
  depends_on = [module.application]
}

module "postgres" {
  source = "./modules/postgres"
  kubeconfig = module.kind_cluster.kubeconfig_path
  ansible_python_interpreter = module.kind_cluster.ansible_python_interpreter
  depends_on = [module.nginx]
}

module "minio" {
  source = "./modules/minio"
  kubeconfig = module.kind_cluster.kubeconfig_path
  ansible_python_interpreter = module.kind_cluster.ansible_python_interpreter
  depends_on = [module.nginx]
}

module "gitea" {
  source = "./modules/gitea"
  kubeconfig = module.kind_cluster.kubeconfig_path
  ansible_python_interpreter = module.kind_cluster.ansible_python_interpreter
  depends_on = [module.minio]
}

module "argocd" {
  source = "./modules/argocd"
  kubeconfig = module.kind_cluster.kubeconfig_path
  ansible_python_interpreter = module.kind_cluster.ansible_python_interpreter
  depends_on = [module.gitea]
}

module "airflow" {
  source = "./modules/airflow"
  kubeconfig = module.kind_cluster.kubeconfig_path
  ansible_python_interpreter = module.kind_cluster.ansible_python_interpreter
  depends_on = [module.argocd]
}
