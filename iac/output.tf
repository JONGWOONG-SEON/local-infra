output "kubeconfig_path" {
  description = "The absolute path to the generated kubeconfig"
  value       = abspath("${path.module}/kubeconfig.yaml")
}
output "ansible_python_interpreter" {
  description = "Python virtual Interpreter"
  value       = abspath("${path.root}/venv/bin/python")
}
