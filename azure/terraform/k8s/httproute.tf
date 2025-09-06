resource "kubernetes_manifest" "httproute" {
  count = var.create_custom_resources ? 1 : 0

  manifest = {
    apiVersion = "gateway.networking.k8s.io/v1"
    kind       = "HTTPRoute"
    metadata = {
      name      = "vllm-route"
      namespace = kubernetes_namespace.vllm.metadata[0].name
    }
    spec = {
      parentRefs = [{
        name      = "public-gateway"
        namespace = "ngf"
        # sectionName = "http"   # uncomment if your Gateway has multiple listeners
      }]
      rules = [{
        matches = [{
          path = {
            type  = "PathPrefix"
            value = "/"
          }
        }]
        backendRefs = [{
          name = kubernetes_service.svc.metadata[0].name
          port = 80
        }]
      }]
    }
  }
  depends_on = [
    kubernetes_manifest.public_gateway,
    kubernetes_service.svc
  ]
}
