resource "helm_release" "nvidia_device_plugin" {
  name             = "nvidia-device-plugin"
  repository       = "https://nvidia.github.io/k8s-device-plugin"
  chart            = "nvidia-device-plugin"
  version          = "0.16.2"
  namespace        = "kube-system"
  create_namespace = false
  wait             = true
  timeout          = 600

  values = [yamlencode({
    nodeSelector = {
      "cloud.google.com/gke-accelerator" = "nvidia-l4"
    }
    tolerations = [
      {
        key      = "nvidia.com/gpu"
        operator = "Exists"
        effect   = "NoSchedule"
      }
    ]
    # optional: args to be more forgiving on startup
    args = ["--fail-on-init-error=false"]
  })]
}
