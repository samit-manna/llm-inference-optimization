# Upload a Model that references our GAR image and container contract
# Using gcloud until first-class TF resource covers this cleanly

resource "null_resource" "upload_model" {
  triggers = {
    image_uri               = var.image_uri
    model_display_name      = var.model_display_name
    project_id              = var.project_id
    region                  = var.region
    env_hash                = sha1(jsonencode(var.container_env))
    predict_route           = var.container_predict_route
    health_route            = var.container_health_route
    container_port          = tostring(var.container_port)
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      mkdir -p .terraform-artifacts
      TMP_MODEL_INFO=.terraform-artifacts/model.json
      # Build env vars string KEY=VALUE,KEY=VALUE
      ENV_VARS=$(python3 - <<'PY'
import json, os
env = json.loads(os.environ['TF_VAR_CONTAINER_ENV_JSON'])
print(','.join([f"{k}={v}" for k,v in env.items()]))
PY
)
      gcloud ai models upload \
        --project ${var.project_id} \
        --region ${var.region} \
        --display-name "${var.model_display_name}" \
        --container-image-uri "${var.image_uri}" \
        --container-ports ${var.container_port} \
        --container-predict-route "${var.container_predict_route}" \
        --container-health-route "${var.container_health_route}" \
        --container-env-vars "$ENV_VARS" \
        --format=json > "$TMP_MODEL_INFO"

      # Extract the fully-qualified model resource name into a plain-text file for Terraform to consume reliably
      jq -r '.model' "$TMP_MODEL_INFO" > .terraform-artifacts/MODEL_NAME
      echo "Model uploaded: $(cat .terraform-artifacts/MODEL_NAME)"
    EOT
    environment = {
      TF_VAR_CONTAINER_ENV_JSON = jsonencode(var.container_env)
    }
    interpreter = ["/bin/bash", "-c"]
  }

  depends_on = [
    google_vertex_ai_endpoint.endpoint,
    google_artifact_registry_repository.repo,
    google_project_iam_member.aiplatform_sa_gar_reader
  ]
}

# Read back the model resource name from the artifact file
data "local_file" "model_name_txt" {
  filename   = "${path.module}/.terraform-artifacts/MODEL_NAME"
  depends_on = [null_resource.upload_model]
}

locals {
  model_name = chomp(try(data.local_file.model_name_txt.content, ""))
}
