resource "aws_iam_role" "codepipeline_role" {
  count = var.codecommit_name != "" ? 1 : 0
  name  = "${local.name_prefix}-codepipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "codepipeline.amazonaws.com" },
        Action    = "sts:AssumeRole",
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_policy" "codepipeline_policy" {
  count = var.codecommit_name != "" ? 1 : 0
  name  = "${local.name_prefix}-codepipeline-policy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetBucketVersioning",
          "s3:ListBucket"
        ],
        Resource = [
          aws_s3_bucket.codedeploy_bundles.arn,
          "${aws_s3_bucket.codedeploy_bundles.arn}/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "codebuild:StartBuild",
          "codebuild:BatchGetBuilds"
        ],
        Resource = [aws_codebuild_project.discord_build[0].arn]
      },
      {
        Effect = "Allow",
        Action = [
          "codedeploy:CreateDeployment",
          "codedeploy:GetApplication",
          "codedeploy:GetDeploymentGroup",
          "codedeploy:GetDeploymentConfig",
          "codedeploy:RegisterApplicationRevision",
          "codedeploy:GetDeployment",
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "codecommit:GetBranch",
          "codecommit:GetCommit",
          "codecommit:GitPull",
          "codecommit:UploadArchive",
          "codecommit:GetUploadArchiveStatus"
        ],
        Resource = var.codecommit_name != "" ? aws_codecommit_repository.discord[0].arn : "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codepipeline_role_attach" {
  count      = var.codecommit_name != "" ? 1 : 0
  role       = aws_iam_role.codepipeline_role[0].name
  policy_arn = aws_iam_policy.codepipeline_policy[0].arn
}

resource "aws_codepipeline" "discord_pipeline" {
  count    = var.codecommit_name != "" ? 1 : 0
  name     = "${local.name_prefix}-pipeline"
  role_arn = aws_iam_role.codepipeline_role[0].arn

  artifact_store {
    location = aws_s3_bucket.codedeploy_bundles.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      output_artifacts = ["SourceArtifact"]
      configuration = {
        RepositoryName = var.codecommit_name
        BranchName     = "main"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["SourceArtifact"]
      output_artifacts = ["BuildArtifact"]
      configuration = {
        ProjectName = aws_codebuild_project.discord_build[0].name
      }
    }
  }



  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CodeDeploy"
      version         = "1"
      input_artifacts = ["BuildArtifact"]
      configuration = {
        ApplicationName     = aws_codedeploy_app.discord_bot_app.name
        DeploymentGroupName = aws_codedeploy_deployment_group.discord_bot_deployment_group.deployment_group_name
      }
    }
  }

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "codecommit_trigger" {
  count = var.codecommit_name != "" ? 1 : 0
  name  = "${local.name_prefix}-codecommit-trigger"

  event_pattern = jsonencode({
    source      = ["aws.codecommit"]
    detail-type = ["CodeCommit Repository State Change"]
    resources   = [aws_codecommit_repository.discord[0].arn]
    detail = {
      event         = ["referenceCreated", "referenceUpdated"]
      referenceType = ["branch"]
      referenceName = ["main"]
    }
  })

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "codepipeline_target" {
  count    = var.codecommit_name != "" ? 1 : 0
  rule     = aws_cloudwatch_event_rule.codecommit_trigger[0].name
  arn      = aws_codepipeline.discord_pipeline[0].arn
  role_arn = aws_iam_role.eventbridge_pipeline_role[0].arn
}

resource "aws_iam_role" "eventbridge_pipeline_role" {
  count = var.codecommit_name != "" ? 1 : 0
  name  = "${local.name_prefix}-eventbridge-pipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "events.amazonaws.com" },
        Action    = "sts:AssumeRole",
      }
    ]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "eventbridge_pipeline_policy" {
  count = var.codecommit_name != "" ? 1 : 0
  role  = aws_iam_role.eventbridge_pipeline_role[0].id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "codepipeline:StartPipelineExecution"
        ],
        Resource = aws_codepipeline.discord_pipeline[0].arn
      }
    ]
  })
}
