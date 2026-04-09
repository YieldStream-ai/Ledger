terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ─── ECR Repository ──────────────────────────────────────────────────────────

resource "aws_ecr_repository" "app" {
  name                 = var.app_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ─── IAM Role for Lambda ─────────────────────────────────────────────────────

resource "aws_iam_role" "lambda" {
  name = "${var.app_name}-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ─── CloudWatch Logs ──────────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.app_name}"
  retention_in_days = 14
}

# ─── Lambda Function (container image) ────────────────────────────────────────

resource "aws_lambda_function" "app" {
  function_name = var.app_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.app.repository_url}:latest"
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      GOOGLE_AI_API_KEY   = var.google_ai_api_key
      LLAMA_CLOUD_API_KEY = var.llama_cloud_api_key
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# ─── API Gateway (HTTP API — cheaper than REST API) ──────────────────────────

resource "aws_apigatewayv2_api" "app" {
  name          = var.app_name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.app.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.app.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.app.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.app.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 10  # max concurrent requests
    throttling_rate_limit  = 5   # requests per second sustained
  }
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.app.execution_arn}/*/*"
}

# ─── Fargate (commented out — uncomment if you need always-on for OCR/scanned docs) ─
#
# data "aws_vpc" "default" {
#   default = true
# }
#
# data "aws_subnets" "default" {
#   filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.default.id]
#   }
# }
#
# resource "aws_security_group" "ecs" {
#   name        = "${var.app_name}-ecs-sg"
#   description = "ECS tasks security group"
#   vpc_id      = data.aws_vpc.default.id
#
#   ingress {
#     from_port   = var.container_port
#     to_port     = var.container_port
#     protocol    = "tcp"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
#
#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
# }
#
# resource "aws_ecs_cluster" "app" {
#   name = var.app_name
# }
#
# resource "aws_ecs_task_definition" "app" {
#   family                   = var.app_name
#   network_mode             = "awsvpc"
#   requires_compatibilities = ["FARGATE"]
#   cpu                      = var.cpu
#   memory                   = var.memory
#   execution_role_arn       = aws_iam_role.ecs_execution.arn
#   task_role_arn            = aws_iam_role.ecs_task.arn
#
#   container_definitions = jsonencode([{
#     name  = var.app_name
#     image = "${aws_ecr_repository.app.repository_url}:latest"
#     portMappings = [{ containerPort = var.container_port, protocol = "tcp" }]
#     environment = [
#       { name = "PORT", value = tostring(var.container_port) },
#       { name = "GOOGLE_AI_API_KEY", value = var.google_ai_api_key },
#       { name = "LLAMA_CLOUD_API_KEY", value = var.llama_cloud_api_key },
#     ]
#     logConfiguration = {
#       logDriver = "awslogs"
#       options = {
#         "awslogs-group"         = aws_cloudwatch_log_group.app.name
#         "awslogs-region"        = var.aws_region
#         "awslogs-stream-prefix" = "ecs"
#       }
#     }
#   }])
# }
#
# resource "aws_ecs_service" "app" {
#   name            = var.app_name
#   cluster         = aws_ecs_cluster.app.id
#   task_definition = aws_ecs_task_definition.app.arn
#   desired_count   = var.desired_count
#   launch_type     = "FARGATE"
#   network_configuration {
#     subnets          = data.aws_subnets.default.ids
#     security_groups  = [aws_security_group.ecs.id]
#     assign_public_ip = true
#   }
# }
