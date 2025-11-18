resource "aws_iam_role" "codebuild_role" {
  count = 1
  name = "discord-codebuild-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { Service = "codebuild.amazonaws.com" }
        Action = "sts:AssumeRole"
      }
    ]
  })
  tags = local.common_tags
}

resource "aws_iam_role_policy" "codebuild_policy" {
  count = 1
  name = "discord-codebuild-policy"
  role = aws_iam_role.codebuild_role[0].id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:GetBucketLocation",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.codedeploy_bundles.arn,
          "${aws_s3_bucket.codedeploy_bundles.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_codebuild_project" "discord_build" {
  count = 1
  name = "discord-bot-build"

  service_role = aws_iam_role.codebuild_role[0].arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type = "BUILD_GENERAL1_MEDIUM"
    image = "aws/codebuild/standard:6.0"
    type  = "LINUX_CONTAINER"
    privileged_mode = true
    environment_variable {
      name  = "ECR_REPO"
      value = var.ecr_repo
    }
    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }
  }

  source {
    type  = "CODEPIPELINE"
    buildspec = file("${path.module}/../buildspec.yml")
  }

  tags = local.common_tags
}
