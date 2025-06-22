variable "kubeconfig" {}
variable "ansible_python_interpreter" {}

resource "null_resource" "deploy_gitea"{
  provisioner "local-exec" {
    command = <<-EOT
      ansible-playbook -i localhost, -e kubeconfig=${var.kubeconfig} -e ansible_python_interpreter=${var.ansible_python_interpreter} ${path.module}/playbook_gitea.yaml
      ansible-playbook -i localhost, -e kubeconfig=${var.kubeconfig} -e ansible_python_interpreter=${var.ansible_python_interpreter} ${path.module}/playbook_runner.yaml
    EOT
  }
}

