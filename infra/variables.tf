variable "aws_region" {
  description = "AWS region"
  default     = "us-west-2"
}

variable "app_name" {
  description = "Application name"
  default     = "yieldstream-qualify"
}

variable "container_port" {
  description = "Port the container listens on (used by Fargate if re-enabled)"
  default     = 8100
}

variable "google_ai_api_key" {
  description = "Google AI API key for Gemini enrichment"
  type        = string
  sensitive   = true
  default     = ""
}

variable "llama_cloud_api_key" {
  description = "LlamaParse API key (Tier 4 fallback)"
  type        = string
  sensitive   = true
  default     = ""
}

# Fargate vars — only needed if you uncomment Fargate in main.tf
# variable "cpu" {
#   default = 256
# }
# variable "memory" {
#   default = 512
# }
# variable "desired_count" {
#   default = 1
# }
