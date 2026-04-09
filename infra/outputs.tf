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

    # Update Lambda to use new image
    aws lambda update-function-code --function-name ${var.app_name} --image-uri ${aws_ecr_repository.app.repository_url}:latest --region ${var.aws_region}
  EOT
}
