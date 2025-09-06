# Advanced autoscaling using CloudWatch Math expressions
# This calculates true aggregate tokens per second across all concurrent requests

resource "aws_appautoscaling_target" "ep" {
  max_capacity       = 8
  min_capacity       = 1
  resource_id        = "endpoint/${aws_sagemaker_endpoint.ep.name}/variant/AllTraffic"
  scalable_dimension = "sagemaker:variant:DesiredInstanceCount"
  service_namespace  = "sagemaker"
}

resource "aws_cloudwatch_metric_alarm" "aggregate_tps_scale_out" {
  alarm_name          = "${var.name}-aggregate-tps-scale-out"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  threshold           = "1200"  # Scale out when aggregate TPS > 800
  alarm_description   = "Scale out when aggregate tokens per second is high"
  alarm_actions       = [aws_appautoscaling_policy.step_scale_out.arn]

  metric_query {
    id          = "m1"
    return_data = "false"
    metric {
      metric_name = "TokensGenerated"
      namespace   = "LLM/Serving"
      period      = "60"
      stat        = "Sum"
      dimensions = {
        EndpointName = aws_sagemaker_endpoint.ep.name
      }
    }
  }

  metric_query {
    id          = "m2"
    return_data = "false"
    metric {
      metric_name = "RequestCount"
      namespace   = "LLM/Serving"
      period      = "60"
      stat        = "Sum"
      dimensions = {
        EndpointName = aws_sagemaker_endpoint.ep.name
      }
    }
  }

  # Calculate aggregate tokens per second: total_tokens / 60_seconds
  metric_query {
    id          = "e1"
    return_data = "true"
    expression  = "m1/60"
    label       = "Aggregate Tokens Per Second"
  }
}

resource "aws_cloudwatch_metric_alarm" "aggregate_tps_scale_in" {
  alarm_name          = "${var.name}-aggregate-tps-scale-in"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "5"  # Wait longer before scaling in
  threshold           = "200"
  alarm_description   = "Scale in when aggregate tokens per second is low"
  alarm_actions       = [aws_appautoscaling_policy.step_scale_in.arn]

  metric_query {
    id          = "m1"
    return_data = "false"
    metric {
      metric_name = "TokensGenerated"
      namespace   = "LLM/Serving"
      period      = "60"
      stat        = "Sum"
      dimensions = {
        EndpointName = aws_sagemaker_endpoint.ep.name
      }
    }
  }

  metric_query {
    id          = "e1"
    return_data = "true"
    expression  = "m1/60"
    label       = "Aggregate Tokens Per Second"
  }
}

# Step scaling policies for more granular control
resource "aws_appautoscaling_policy" "step_scale_out" {
  name               = "${var.name}-step-scale-out"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ep.resource_id
  scalable_dimension = aws_appautoscaling_target.ep.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ep.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      metric_interval_upper_bound = 300  # 700-1000 TPS
      scaling_adjustment          = 1    # Add 1 instance
    }

    step_adjustment {
      metric_interval_lower_bound = 300  # > 1000 TPS
      scaling_adjustment          = 1    # Add 1 instance
    }
  }
}

resource "aws_appautoscaling_policy" "step_scale_in" {
  name               = "${var.name}-step-scale-in"
  policy_type        = "StepScaling"
  resource_id        = aws_appautoscaling_target.ep.resource_id
  scalable_dimension = aws_appautoscaling_target.ep.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ep.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown               = 300  # Longer cooldown for scale-in
    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = -1
    }
  }
}
