output "endpoint_name" {
  value = google_vertex_ai_endpoint.endpoint.name
}

output "endpoint_id" {
  # name is like projects/…/locations/…/endpoints/1234567890 → extract the ID for convenience
  #value = regex(".*/endpoints/(.*)$", google_vertex_ai_endpoint.endpoint.name)[0]
  value = google_vertex_ai_endpoint.endpoint.name
}

output "model_name" {
  value = local.model_name
}
