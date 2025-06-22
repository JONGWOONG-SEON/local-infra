variable "kubeconfig" {}
variable "ansible_python_interpreter" {}

resource "null_resource" "deploy_airflow"{
  provisioner "local-exec" {
    command = <<-EOT
      ansible-playbook -i localhost, -e kubeconfig=${var.kubeconfig} -e ansible_python_interpreter=${var.ansible_python_interpreter} ${path.module}/playbook_gitsync.yaml
      ansible-playbook -i localhost, -e kubeconfig=${var.kubeconfig} -e ansible_python_interpreter=${var.ansible_python_interpreter} ${path.module}/playbook_airflow.yaml
    EOT
  }
}
