resource "kubernetes_manifest" "keda_scaledobject" {
  count = var.create_custom_resources ? 1 : 0

  manifest = {
    apiVersion = "keda.sh/v1alpha1"
    kind       = "ScaledObject"
    metadata = {
      name      = "vllm-tokens-scaler"
      namespace = kubernetes_namespace.vllm.metadata[0].name
    }
    spec = {
      scaleTargetRef = {
        name = kubernetes_deployment.vllm.metadata[0].name
      }
      minReplicaCount = 1
      maxReplicaCount = 6
      cooldownPeriod  = 90
      triggers = [{
        type = "prometheus"
        metadata = {
          serverAddress       = "http://prometheus-operated.monitoring.svc:9090"
          metricName          = "llm_completion_tokens_per_min"
          query               = "rate(llm_completion_tokens_total[1m]) * 60"
          threshold           = tostring(var.tokens_per_min_threshold)
          activationThreshold = "8000"
        }
      }]
      advanced = {
        horizontalPodAutoscalerConfig = {
          behavior = {
            scaleUp = {
              stabilizationWindowSeconds = 60
              policies = [{
                type          = "Percent"
                value         = "100"
                periodSeconds = 60
              }]
            }
            scaleDown = {
              stabilizationWindowSeconds = 120
              policies = [{
                type          = "Percent"
                value         = "50"
                periodSeconds = 60
              }]
            }
          }
        }
      }
    }
  }

  depends_on = [kubernetes_deployment.vllm]
}
