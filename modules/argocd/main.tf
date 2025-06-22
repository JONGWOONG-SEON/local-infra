variable "kubeconfig" {}
variable "ansible_python_interpreter" {}

resource "null_resource" "deploy_argocd"{
  provisioner "local-exec" {
    command = <<-EOT
      ansible-playbook -i localhost, -e "kubeconfig=${var.kubeconfig}" -e "ansible_python_interpreter=${var.ansible_python_interpreter}" ${path.module}/playbook_argocd.yaml --extra-vars "@./vars/ansible-argocd.yaml"
    EOT
  }
}

