# ─── Terraform remote-state bootstrap ────────────────────────────────────────
#
# Creates the S3 bucket that stores the main stack's state (see infra/backend.tf).
# Applied once, by hand, with local state: the backend bucket can't store the
# state of the config that creates it (chicken-and-egg).
#
#   cd infra/bootstrap && terraform init && terraform apply
#
# Locking uses S3's native lockfile (use_lockfile = true, Terraform ≥ 1.10),
# so no DynamoDB lock table is needed.

terraform {
  required_version = ">= 1.10"
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

variable "aws_region" {
  description = "AWS region (must match infra/backend.tf)"
  default     = "us-west-2"
}

variable "app_name" {
  description = "Application name (must match infra/variables.tf)"
  default     = "yieldstream-ledger"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "tfstate" {
  bucket = "${var.app_name}-tfstate-${data.aws_caller_identity.current.account_id}"

  # Losing this bucket means Terraform forgets every resource it manages
  lifecycle {
    prevent_destroy = true
  }
}

# Every state write is a new version, so a bad apply can be rolled back
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# State contains secrets (Lambda env vars), so encrypt and block public access
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Keep old state versions for 90 days, not forever
resource "aws_s3_bucket_lifecycle_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    id     = "expire-old-state-versions"
    status = "Enabled"
    filter {}
    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
  depends_on = [aws_s3_bucket_versioning.tfstate]
}

output "state_bucket" {
  description = "Use as `bucket` in infra/backend.tf"
  value       = aws_s3_bucket.tfstate.bucket
}
