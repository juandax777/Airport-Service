output "broker" {
  value = {
    arn             = aws_mq_broker.this.arn
    amqps_endpoints = distinct(flatten(aws_mq_broker.this.instances[*].endpoints))
    console_urls    = distinct(aws_mq_broker.this.instances[*].console_url)
  }
}
