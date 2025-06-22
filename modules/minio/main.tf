variable "kubeconfig" {}
variable "ansible_python_interpreter" {}

resource "null_resource" "deploy_minio"{
  provisioner "local-exec" {
    command = <<-EOT
      ansible-playbook -i localhost, -e kubeconfig=${var.kubeconfig} ${path.module}/playbook_minio.yaml
    EOT
  }
}

