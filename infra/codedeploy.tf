resource "aws_codedeploy_app" "discord_bot_app" {
  name             = "discord-bot-app"
  compute_platform = "Server"
  tags             = local.tags
}

resource "aws_codedeploy_deployment_group" "discord_bot_deployment_group" {
  app_name              = aws_codedeploy_app.discord_bot_app.name
  deployment_group_name = "discord-bot-deployment-group"

  service_role_arn = aws_iam_role.codedeploy_service_role.arn

  deployment_config_name = "CodeDeployDefault.OneAtATime"

  ec2_tag_set {
    ec2_tag_filter {
      key   = "Name"
      value = "discord-bot-instance"
      type  = "KEY_AND_VALUE"
    }
  }

  auto_rollback_configuration {
    enabled = true
    events  = ["DEPLOYMENT_FAILURE"]
  }
  tags = local.tags
}
