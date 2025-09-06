resource "kubernetes_deployment" "vllm" {
  metadata {
    name      = "vllm"
    namespace = kubernetes_namespace.vllm.metadata[0].name
    labels    = { app = "vllm" }
    annotations = {
      "prometheus.io/scrape" = "true"
      "prometheus.io/port"   = "9000"
      "prometheus.io/path"   = "/metrics"
    }
  }
  spec {
    replicas = 1
    selector { match_labels = { app = "vllm" } }
    template {
      metadata { labels = { app = "vllm" } }
      spec {
        # GKE L4 nodes advertise this label
        node_selector = { "cloud.google.com/gke-accelerator" = "nvidia-l4" }

        toleration {
          key      = "nvidia.com/gpu"
          operator = "Exists"
          effect   = "NoSchedule"
        }

        container {
          name  = "vllm"
          image = var.vllm_image
          
          security_context {
            capabilities {
              add = ["SYS_ADMIN"]
            }
          }
          
          args = [
            "--host", "0.0.0.0", "--port", "8000",
            "--model", "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
            "--max-model-len", "8192",
            "--gpu-memory-utilization", "0.95",
            "--enforce-eager",
            "--trust-remote-code",
            "--disable-log-requests",
            "--served-model-name", "llama",
            "--max-num-batched-tokens", "32768",
            "--max-num-seqs", "160",
            "--device", "cuda"
          ]
          env {
            name = "HUGGING_FACE_HUB_TOKEN"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.hf.metadata[0].name
                key  = "token"
              }
            }
          }
          port { container_port = 8000 }
          resources {
            limits = {
              "nvidia.com/gpu" = "1"
              cpu              = "6"
              memory           = "30Gi"
            }
            requests = {
              "nvidia.com/gpu" = "1"
              cpu              = "4"
              memory           = "24Gi"
            }
          }
          volume_mount {
            name       = "cache"
            mount_path = "/tmp"
          }
          volume_mount {
            name       = "shm"
            mount_path = "/dev/shm"
          }
        }

        container {
          name  = "proxy"
          image = var.proxy_image
          env {
            name  = "TARGET_URL"
            value = "http://localhost:8000/v1/chat/completions"
          }
          env {
            name  = "INSTANCE_HOURLY_USD"
            value = tostring(var.instance_hourly_usd)
          }
          port { container_port = 9000 }
          readiness_probe {
            http_get {
              path = "/metrics"
              port = 9000
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }
          volume_mount {
            name       = "cache"
            mount_path = "/tmp"
          }
        }

        volume {
          name     = "cache"
          empty_dir {}
        }
        volume {
          name      = "shm"
          empty_dir {
            medium     = "Memory"
            size_limit = "2Gi"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "svc" {
  metadata {
    name      = "vllm-svc"
    namespace = kubernetes_namespace.vllm.metadata[0].name
    labels    = { app = "vllm" }
  }
  spec {
    type     = "LoadBalancer"
    selector = { app = "vllm" }
    port {
      name        = "http"
      port        = 80
      target_port = 9000
    }
  }
}
