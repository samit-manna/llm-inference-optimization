resource "kubernetes_namespace" "vllm" {
  metadata {
    name = "vllm"
  }
}

resource "kubernetes_secret" "hf" {
  metadata {
    name      = "hf-token"
    namespace = kubernetes_namespace.vllm.metadata[0].name
  }
  data = {
    token = var.hf_token
  }
  type = "Opaque"
}
