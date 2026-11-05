# ─── Async parse jobs ─────────────────────────────────────────────────────────
#
#   POST /jobs ──► presigned POST ──► S3 uploads/{job_id}.pdf
#   S3 ObjectCreated ──► SQS jobs ──► worker Lambda ──► S3 results/{job_id}.json
#                         └─(3 failed receives)─► SQS DLQ ──► CloudWatch alarm
#   Job state: DynamoDB (PENDING_UPLOAD → PROCESSING → COMPLETED | FAILED)

data "aws_caller_identity" "current" {}

locals {
  jobs_name           = "${var.app_name}-jobs"
  worker_name         = "${var.app_name}-worker"
  worker_timeout      = 300
  queue_visibility    = local.worker_timeout * 6 # AWS guidance: ≥ 6× function timeout for SQS sources
  dlq_max_receive     = 3
  worker_max_parallel = 5 # caps concurrent parses (protects Gemini's 15 RPM limit)
}

# ─── S3 bucket ────────────────────────────────────────────────────────────────

resource "aws_s3_bucket" "jobs" {
  bucket        = "${local.jobs_name}-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "jobs" {
  bucket                  = aws_s3_bucket.jobs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "jobs" {
  bucket = aws_s3_bucket.jobs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "jobs" {
  bucket = aws_s3_bucket.jobs.id

  rule {
    id     = "expire-uploads"
    status = "Enabled"
    filter {
      prefix = "uploads/"
    }
    expiration {
      days = 7
    }
  }

  rule {
    id     = "expire-results"
    status = "Enabled"
    filter {
      prefix = "results/"
    }
    expiration {
      days = 30
    }
  }
}

# Browsers upload straight to S3 with the presigned POST
resource "aws_s3_bucket_cors_configuration" "jobs" {
  bucket = aws_s3_bucket.jobs.id
  cors_rule {
    allowed_methods = ["POST"]
    allowed_origins = var.frontend_origins
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }
}

# ─── SQS queue + dead-letter queue ────────────────────────────────────────────

resource "aws_sqs_queue" "jobs_dlq" {
  name                      = "${local.jobs_name}-dlq"
  message_retention_seconds = 14 * 24 * 60 * 60
}

resource "aws_sqs_queue" "jobs" {
  name                       = local.jobs_name
  visibility_timeout_seconds = local.queue_visibility
  message_retention_seconds  = 4 * 24 * 60 * 60

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jobs_dlq.arn
    maxReceiveCount     = local.dlq_max_receive
  })
}

# Only this bucket (in this account) may publish to the queue
resource "aws_sqs_queue_policy" "jobs" {
  queue_url = aws_sqs_queue.jobs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowJobsBucketNotifications"
      Effect    = "Allow"
      Principal = { Service = "s3.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.jobs.arn
      Condition = {
        ArnEquals    = { "aws:SourceArn" = aws_s3_bucket.jobs.arn }
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
      }
    }]
  })
}

resource "aws_s3_bucket_notification" "jobs" {
  bucket = aws_s3_bucket.jobs.id

  queue {
    queue_arn     = aws_sqs_queue.jobs.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "uploads/"
    filter_suffix = ".pdf"
  }

  depends_on = [aws_sqs_queue_policy.jobs]
}

# ─── DynamoDB job table ───────────────────────────────────────────────────────

resource "aws_dynamodb_table" "jobs" {
  name         = local.jobs_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}

# ─── Worker Lambda (same image as the API, different handler) ────────────────

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/aws/lambda/${local.worker_name}"
  retention_in_days = 14
}

resource "aws_iam_role" "worker" {
  name = "${local.worker_name}-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Logs + SQS receive/delete for the event source mapping
resource "aws_iam_role_policy_attachment" "worker_sqs" {
  role       = aws_iam_role.worker.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole"
}

resource "aws_iam_role_policy" "worker_jobs" {
  name = "jobs-access"
  role = aws_iam_role.worker.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadUploads"
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.jobs.arn}/uploads/*"
      },
      {
        Sid      = "WriteResults"
        Effect   = "Allow"
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.jobs.arn}/results/*"
      },
      {
        Sid      = "UpdateJobState"
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
        Resource = aws_dynamodb_table.jobs.arn
      },
    ]
  })
}

resource "aws_lambda_function" "worker" {
  function_name = local.worker_name
  role          = aws_iam_role.worker.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.app.repository_url}:latest"
  timeout       = local.worker_timeout
  memory_size   = 1024

  image_config {
    command = ["worker_handler.handler"]
  }

  environment {
    variables = {
      GOOGLE_AI_API_KEY   = var.google_ai_api_key
      LLAMA_CLOUD_API_KEY = var.llama_cloud_api_key
      JOBS_BUCKET         = aws_s3_bucket.jobs.bucket
      JOBS_TABLE          = aws_dynamodb_table.jobs.name
    }
  }

  lifecycle {
    ignore_changes = [image_uri] # deployed by CI, see main.tf
  }

  depends_on = [aws_cloudwatch_log_group.worker]
}

resource "aws_lambda_event_source_mapping" "worker" {
  event_source_arn        = aws_sqs_queue.jobs.arn
  function_name           = aws_lambda_function.worker.arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]

  scaling_config {
    maximum_concurrency = local.worker_max_parallel
  }

  depends_on = [aws_iam_role_policy_attachment.worker_sqs]
}

# ─── API Lambda access to jobs (role defined in main.tf) ─────────────────────

resource "aws_iam_role_policy" "api_jobs" {
  name = "jobs-access"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Presigned POSTs are signed with this role, so it needs PutObject itself
        Sid      = "PresignUploads"
        Effect   = "Allow"
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.jobs.arn}/uploads/*"
      },
      {
        Sid      = "ReadResults"
        Effect   = "Allow"
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.jobs.arn}/results/*"
      },
      {
        Sid      = "CreateAndReadJobs"
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem"]
        Resource = aws_dynamodb_table.jobs.arn
      },
    ]
  })
}

# ─── Alerting ─────────────────────────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "jobs_dlq" {
  alarm_name          = "${local.jobs_name}-dlq-not-empty"
  alarm_description   = "A parse job failed ${local.dlq_max_receive} times and landed in the DLQ."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.jobs_dlq.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
}
