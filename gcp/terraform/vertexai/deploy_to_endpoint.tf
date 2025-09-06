# Deploy uploaded model to the created Endpoint with L4 accelerator
resource "null_resource" "deploy_model" {
  triggers = {
    endpoint_name     = google_vertex_ai_endpoint.endpoint.name
    model_name        = local.model_name
    machine_type      = var.machine_type
    accelerator_type  = var.accelerator_type
    accelerator_count = tostring(var.accelerator_count)
    min_replica       = tostring(var.min_replica)
    max_replica       = tostring(var.max_replica)
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      gcloud ai endpoints deploy-model "${google_vertex_ai_endpoint.endpoint.name}" \
        --project ${var.project_id} \
        --region ${var.region} \
        --model "${local.model_name}" \
        --display-name "${var.model_display_name}-deployment" \
        --traffic-split=0=100 \
        --machine-type "${var.machine_type}" \
        --accelerator=type=${var.accelerator_type},count=${var.accelerator_count} \
        --min-replica-count ${var.min_replica} \
        --max-replica-count ${var.max_replica} \
        --enable-access-logging
    EOT
    interpreter = ["/bin/bash", "-c"]
  }

  depends_on = [null_resource.upload_model]
}
