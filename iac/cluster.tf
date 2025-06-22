resource "null_resource" "kind_cluster" {
  provisioner "local-exec" {
    command = <<-EOT
      kind create cluster --name=local-cluster --config=${path.module}/kind-config.yaml
      kind get kubeconfig --name=local-cluster > ${path.module}/kubeconfig.yaml
      docker network connect kind registry.local || true
    EOT
  }

  triggers = {
    always_run = "true"
  }
}

resource "null_resource" "destroy_kind_cluster" {
  provisioner "local-exec" {
    when    = destroy
    command = "kind delete cluster --name=local-cluster && rm -f ${path.module}/kubeconfig.yaml"
  }

  lifecycle {
    prevent_destroy = false
    create_before_destroy = false
    ignore_changes = [triggers]
  }

  triggers = {
    noop = "fixed-value"
  }

  depends_on = [null_resource.kind_cluster]
}

