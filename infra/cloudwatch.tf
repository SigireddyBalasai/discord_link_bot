resource "aws_cloudwatch_log_group" "discord_bot_logs" {
  name              = "/discord-bot/logs"
  retention_in_days = 7
  tags              = local.tags
  skip_destroy      = true
}
