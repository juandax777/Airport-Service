resource "aws_cloudwatch_log_metric_filter" "quarantine" {
  name           = "${var.function_name}-quarantine"
  log_group_name = var.log_group
  pattern        = "\"notification_quarantined\""

  metric_transformation {
    name      = var.function_name
    namespace = "Itineraries/Quarantine"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda" {
  for_each = toset(["Errors", "Throttles"])

  alarm_name          = "${var.function_name}-${lower(each.key)}"
  namespace           = "AWS/Lambda"
  metric_name         = each.key
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_actions

  dimensions = { FunctionName = var.function_name }
}

resource "aws_cloudwatch_metric_alarm" "quarantine" {
  alarm_name          = "${var.function_name}-quarantine"
  namespace           = "Itineraries/Quarantine"
  metric_name         = var.function_name
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 1
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_actions
}
