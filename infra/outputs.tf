output "api_url" {
  description = "API Gateway URL — use this as PARSER_SERVICE_URL in YieldStream"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "ecr_repository_url" {
  description = "ECR repository URL — push Docker images here"
  value       = aws_ecr_repository.app.repository_url
}

output "deploy_commands" {
  description = "Commands to build, push, and deploy"
  value       = <<-EOT
    # Authenticate Docker with ECR
    aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app.repository_url}

    # Build and push (run from YieldStream-Qualify root)
    docker build -t ${var.app_name} .
    docker tag ${var.app_name}:latest ${aws_ecr_repository.app.repository_url}:latest
    docker push ${aws_ecr_repository.app.repository_url}:latest

    # Update both Lambdas (API + async worker) to use the new image
    aws lambda update-function-code --function-name ${var.app_name} --image-uri ${aws_ecr_repository.app.repository_url}:latest --region ${var.aws_region}
    aws lambda update-function-code --function-name ${aws_lambda_function.worker.function_name} --image-uri ${aws_ecr_repository.app.repository_url}:latest --region ${var.aws_region}
  EOT
}

output "jobs_bucket" {
  description = "S3 bucket for async job uploads/results"
  value       = aws_s3_bucket.jobs.bucket
}

output "jobs_table" {
  description = "DynamoDB table holding async job state"
  value       = aws_dynamodb_table.jobs.name
}

output "jobs_queue_url" {
  description = "SQS queue feeding the worker Lambda"
  value       = aws_sqs_queue.jobs.id
}

output "jobs_dlq_url" {
  description = "Dead-letter queue — messages here failed 3 times"
  value       = aws_sqs_queue.jobs_dlq.id
}
