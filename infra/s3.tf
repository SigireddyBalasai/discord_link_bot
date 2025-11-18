resource "aws_s3_bucket" "codedeploy_bundles" {
  bucket = terraform.workspace == "default" ? "discord-bot-codedeploy-bundles-${data.aws_region.current.name}" : "discord-bot-codedeploy-bundles-${data.aws_region.current.name}-${terraform.workspace}"
  # `acl` is deprecated on the bucket resource; use `aws_s3_bucket_acl` resource instead

  # The following features are handled in dedicated resources for newer providers
  # (see aws_s3_bucket_versioning, aws_s3_bucket_lifecycle_configuration, aws_s3_bucket_server_side_encryption_configuration)
  tags = local.common_tags
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

/*
The AWS provider warns about ACLs when the bucket's Object Ownership is
configured to disable ACLs (BucketOwnerEnforced). Since this bucket is used
by CodeDeploy and Policy-based access control is preferred, we remove the
explicit `aws_s3_bucket_acl` resource to avoid failures like
"AccessControlListNotSupported: The bucket does not allow ACLs".

If you need to set a non-default ACL in the future, remove the Object
Ownership setting or manage the ACL off-band with SDK/console where
appropriate. For now we rely on bucket policy and SSE instead of an ACL.
*/

output "s3_bucket_name" {
  value       = aws_s3_bucket.codedeploy_bundles.bucket
  description = "S3 bucket that stores CodeDeploy bundles"
}
