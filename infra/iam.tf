resource "aws_iam_role" "ec2_instance_role" {
  name = "${local.name_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ec2_custom_policy" {
  name = "discord-ec2-extra"
  role = aws_iam_role.ec2_instance_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid = "S3AccessToBundleBucket"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          aws_s3_bucket.codedeploy_bundles.arn,
          "${aws_s3_bucket.codedeploy_bundles.arn}/*"
        ]
      },
      {
        Sid = "CloudWatchLogsWriteAccess"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/${local.name_prefix}/logs:*"
      },
      {
        Sid      = "CodedeployHookAccess"
        Action   = ["codedeploy:PutLifecycleEventHookExecutionStatus"]
        Effect   = "Allow"
        Resource = "arn:aws:codedeploy:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:deploymentgroup:${aws_codedeploy_app.discord_bot_app.name}/${aws_codedeploy_deployment_group.discord_bot_deployment_group.deployment_group_name}"
      },
      {
        Sid      = "SSMParameterAccess"
        Action   = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${local.name_prefix}/*"
      },
      {
        Sid = "DynamoDBAccess"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Effect = "Allow"
        Resource = [
          aws_dynamodb_table.discord_bot_table.arn
        ]
      }
    ]
  })
}




resource "aws_iam_role_policy" "ec2_ecr_policy" {
  count = 1
  name  = "discord-ec2-ecr"
  role  = aws_iam_role.ec2_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = ["ecr:GetAuthorizationToken"],
        Effect   = "Allow",
        Resource = "*"
      },
      {
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ],
        Effect = "Allow",
        Resource = [
          aws_ecr_repository.discord.arn
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_instance" {
  name = "${local.name_prefix}-instance-profile"
  role = aws_iam_role.ec2_instance_role.name
  tags = local.tags
}

resource "aws_iam_role" "codedeploy_service_role" {
  name = "discord-codedeploy-service-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "codedeploy.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "codedeploy_service_attach" {
  role       = aws_iam_role.codedeploy_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSCodeDeployRole"
}

resource "aws_iam_policy" "codedeploy_s3_policy" {
  name        = "codedeploy-s3-deploy-policy"
  description = "Allow CodeDeploy service to read deployment bundle from specific bucket"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ],
        Resource = [
          aws_s3_bucket.codedeploy_bundles.arn,
          "${aws_s3_bucket.codedeploy_bundles.arn}/*"
        ],
        Effect = "Allow"
      }
    ]
  })
  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "codedeploy_s3_read" {
  role       = aws_iam_role.codedeploy_service_role.name
  policy_arn = aws_iam_policy.codedeploy_s3_policy.arn
}
