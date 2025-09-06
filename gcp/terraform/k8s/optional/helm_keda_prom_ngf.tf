# Gateway API CRDs installation
resource "null_resource" "gateway_api_crds" {
  provisioner "local-exec" {
    command = "kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml"
  }

  # Only run if CRDs don't exist
  triggers = {
    always_run = timestamp()
  }
}

# KEDA
resource "helm_release" "keda" {
  name             = "keda"
  repository       = "https://kedacore.github.io/charts"
  chart            = "keda"
  namespace        = "keda"
  create_namespace = true
  version          = "2.14.0"

  # Wait for all resources to be ready
  wait          = true
  wait_for_jobs = true
  timeout       = 300
}

# kube-prometheus-stack (Prom operator + Grafana + Prom)
resource "helm_release" "kps" {
  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = "monitoring"
  create_namespace = true
  version          = "62.6.0"

  # Wait for all resources including CRDs to be ready
  wait          = true
  wait_for_jobs = true
  timeout       = 600

  # keep defaults minimal; it installs ServiceMonitor CRD
  values = [yamlencode({
    grafana = { enabled = true }
    prometheus = {
      prometheusSpec = {
        retention                                 = "15d"
        serviceMonitorSelectorNilUsesHelmValues   = false
        serviceMonitorSelector                    = {}
        serviceMonitorNamespaceSelector           = {}
      }
    }
  })]
}

# NGINX Gateway Fabric
resource "helm_release" "ngf" {
  name             = "nginx-gateway-fabric"
  repository       = "oci://ghcr.io/nginx/charts"
  chart            = "nginx-gateway-fabric"
  namespace        = "ngf"
  create_namespace = true
  version          = "1.6.2"

  # Wait for all resources including CRDs to be ready
  wait          = true
  wait_for_jobs = true
  timeout       = 300

  # Install after Gateway API CRDs
  depends_on = [null_resource.gateway_api_crds]
}

# Wait for CRDs to be fully registered after Helm releases
resource "time_sleep" "wait_for_crds" {
  depends_on = [
    helm_release.keda,
    helm_release.kps,
    helm_release.ngf
  ]

  create_duration = "30s"
}

# Public Gateway (Gateway API resource)
resource "kubernetes_manifest" "public_gateway" {
  count = var.create_custom_resources ? 1 : 0

  manifest = {
    apiVersion = "gateway.networking.k8s.io/v1"
    kind       = "Gateway"
    metadata = {
      name      = "public-gateway"
      namespace = "ngf"
    }
    spec = {
      gatewayClassName = "nginx"
      listeners = [{
        name     = "http"
        port     = 80
        protocol = "HTTP"
        hostname = null
        allowedRoutes = {
          namespaces = {
            from = "All" # <— allow routes from any namespace
            # OR use a selector:
            # selector = { matchLabels = { allow = "true" } }
          }
        }
      }]
    }
  }
}
