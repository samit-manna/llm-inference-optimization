resource "aws_sagemaker_model" "vllm" {
  name               = "${var.name}-model"
  execution_role_arn = aws_iam_role.sagemaker_exec.arn

  depends_on = [time_sleep.wait_for_iam_role]

  primary_container {
    image          = var.lmi_image_uri
    mode           = "SingleModel"
    model_data_url = null

    environment = {
      HF_MODEL_ID            = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
      HUGGING_FACE_HUB_TOKEN = var.hf_token
      SERVING_FRAMEWORK      = "vllm"

      # vLLM engine args optimized for streaming performance:
      OPTION_MAX_MODEL_LEN            = "8192"
      OPTION_GPU_MEMORY_UTILIZATION   = "0.90"  # Slightly lower for better streaming
      OPTION_ENFORCE_EAGER            = "false" # Disable for better streaming
      OPTION_MAX_NUM_BATCHED_TOKENS   = "16384" # Lower for faster streaming
      
      # Streaming optimizations
      OPTION_DISABLE_LOG_STATS        = "true"  # Reduce logging overhead
      OPTION_ENABLE_CHUNKED_PREFILL   = "true"  # Better streaming responsiveness
      
      # DJL/LMI batching controls optimized for streaming:
      MAX_ROLLING_BATCH_SIZE          = "16"    # Higher for better throughput
      MAX_BATCH_TOTAL_TOKENS          = "16384" # Lower for faster iteration
      MAX_BATCH_PREFILL_TOKENS        = "8192"  # Faster prefill

      LOG_LEVEL = "INFO"
    }

  }

  enable_network_isolation = false
}
