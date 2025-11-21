resource "aws_s3_bucket" "codedeploy_bundles" {
  bucket = terraform.workspace == "default" ? "${local.name_prefix}-codedeploy-bundles-${data.aws_region.current.name}" : "${local.name_prefix}-codedeploy-bundles-${data.aws_region.current.name}-${terraform.workspace}"



  tags = local.tags
}

resource "aws_s3_bucket_versioning" "codedeploy_bundles_versioning" {
  bucket = aws_s3_bucket.codedeploy_bundles.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "codedeploy_bundles_lifecycle" {
  bucket = aws_s3_bucket.codedeploy_bundles.id

  rule {
    id     = "expire-old-versions"
    status = "Enabled"
    filter {
      prefix = ""
    }
    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "codedeploy_bundles_sse" {
  bucket = aws_s3_bucket.codedeploy_bundles.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "codedeploy_bundles_block" {
  count = var.block_public_s3 ? 1 : 0

  bucket = aws_s3_bucket.codedeploy_bundles.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}



output "s3_bucket_name" {
  value       = aws_s3_bucket.codedeploy_bundles.bucket
  description = "S3 bucket that stores CodeDeploy bundles"
}
