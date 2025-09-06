resource "kubernetes_manifest" "servicemonitor" {
  count = var.create_custom_resources ? 1 : 0

  manifest = {
    apiVersion = "monitoring.coreos.com/v1"
    kind       = "ServiceMonitor"
    metadata = {
      name      = "vllm-proxy"
      namespace = kubernetes_namespace.vllm.metadata[0].name
    }
    spec = {
      selector = {
        matchLabels = { app = "vllm" }
      }
      endpoints = [{
        port     = "http"
        path     = "/metrics"
        interval = "15s"
      }]
    }
  }

  depends_on = [kubernetes_service.svc]
}
