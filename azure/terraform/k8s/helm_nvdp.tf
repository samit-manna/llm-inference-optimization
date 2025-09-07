# Use direct Kubernetes manifest instead of Helm chart for better AKS compatibility
resource "kubernetes_manifest" "nvidia_device_plugin" {
  manifest = {
    apiVersion = "apps/v1"
    kind       = "DaemonSet"
    metadata = {
      name      = "nvidia-device-plugin-daemonset"
      namespace = "kube-system"
      labels = {
        "k8s-app" = "nvidia-device-plugin"
      }
    }
    spec = {
      selector = {
        matchLabels = {
          name = "nvidia-device-plugin-ds"
        }
      }
      updateStrategy = {
        type = "RollingUpdate"
      }
      template = {
        metadata = {
          labels = {
            name = "nvidia-device-plugin-ds"
          }
        }
        spec = {
          tolerations = [
            {
              key      = "sku"
              value    = "gpu"
              operator = "Equal"
              effect   = "NoSchedule"
            }
          ]
          nodeSelector = {
            sku = "gpu"
          }
          priorityClassName = "system-node-critical"
          containers = [
            {
              image = "nvcr.io/nvidia/k8s-device-plugin:v0.16.2"
              name  = "nvidia-device-plugin-ctr"
              args  = ["--fail-on-init-error=false"]
              securityContext = {
                allowPrivilegeEscalation = false
                capabilities = {
                  drop = ["ALL"]
                }
              }
              volumeMounts = [
                {
                  name      = "device-plugin"
                  mountPath = "/var/lib/kubelet/device-plugins"
                }
              ]
            }
          ]
          volumes = [
            {
              name = "device-plugin"
              hostPath = {
                path = "/var/lib/kubelet/device-plugins"
              }
            }
          ]
        }
      }
    }
  }
}
