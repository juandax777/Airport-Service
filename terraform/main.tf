locals { name = "${var.project_name}-${var.environment}" }
resource "aws_ecr_repository" "airport" { name = "${local.name}/airport-service"; image_scanning_configuration { scan_on_push = true } }
resource "aws_ecr_repository" "itinerary" { name = "${local.name}/itinerary-service"; image_scanning_configuration { scan_on_push = true } }
resource "aws_ecr_repository" "notification" { name = "${local.name}/notification-service"; image_scanning_configuration { scan_on_push = true } }

# The ECS, RDS, Amazon MQ, Lambda, Secrets Manager and CloudWatch modules are intentionally
# added only after network CIDRs and AWS account identifiers are approved. See README.md.
