resource "aws_iam_role" "ec2_instance_role" {
  name = "discord-bot-ec2-role"

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
  tags = local.common_tags
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
          "s3:ListBucket"
        ]
        Effect   = "Allow"
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
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/discord-bot/logs:*"
      },
      {
        Sid = "CodedeployHookAccess"
        Action = ["codedeploy:PutLifecycleEventHookExecutionStatus"]
        Effect = "Allow"
        Resource = "arn:aws:codedeploy:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:deploymentgroup:${aws_codedeploy_app.discord_bot_app.name}/${aws_codedeploy_deployment_group.discord_bot_deployment_group.deployment_group_name}"
      }
    ]
  })
}

/* Optional: allow EC2/agent to read from CodeCommit (if you want to let agents fetch sources)
resource "aws_iam_role_policy" "ec2_codecommit_policy" {
  count = var.codecommit_name != "" ? 1 : 0
  name  = "discord-ec2-codecommit"
  role  = aws_iam_role.ec2_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "codecommit:GetBranch",
          "codecommit:GetPullRequest",
          "codecommit:GitPull"
        ],
        Effect = "Allow",
        Resource = "arn:aws:codecommit:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.codecommit_name}"
      }
    ]
  })
}
*/

/*
 * If an ECR repo name is supplied we add a small policy allowing the instance
 * to pull from that repo. We still require GetAuthorizationToken on * since
 * that action is global and does not support resource-level restrictions.
 */
resource "aws_iam_role_policy" "ec2_ecr_policy" {
  count = var.ecr_repo != "" ? 1 : 0
  name  = "discord-ec2-ecr"
  role  = aws_iam_role.ec2_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = ["ecr:GetAuthorizationToken"],
        Effect = "Allow",
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
          var.ecr_repo != "" ? "arn:aws:ecr:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:repository/${var.ecr_repo}" : aws_ecr_repository.discord[0].arn
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_instance" {
  name = "discord-bot-instance-profile"
  role = aws_iam_role.ec2_instance_role.name
  tags = local.common_tags
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
  tags = local.common_tags
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
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "codedeploy_s3_read" {
  role       = aws_iam_role.codedeploy_service_role.name
  policy_arn = aws_iam_policy.codedeploy_s3_policy.arn
}
