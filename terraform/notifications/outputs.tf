output "worker" {
  value = {
    function_name = aws_lambda_function.worker.function_name
    log_group     = aws_cloudwatch_log_group.worker.name
    mapping_id    = aws_lambda_event_source_mapping.broker.uuid
  }
}
