output "alarm_names" {
  value = concat(values(aws_cloudwatch_metric_alarm.lambda)[*].alarm_name, [
    aws_cloudwatch_metric_alarm.quarantine.alarm_name
  ])
}
