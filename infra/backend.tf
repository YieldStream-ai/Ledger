# Remote state in S3 (bucket created by infra/bootstrap).
# Backend blocks can't use variables, so the bucket name is spelled out.
# use_lockfile: S3-native state locking — a second `apply` waits instead of
# corrupting state (replaces the older DynamoDB lock table pattern).

terraform {
  backend "s3" {
    bucket       = "yieldstream-ledger-tfstate-401811811922"
    key          = "ledger/terraform.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true
  }
}
