resource "aws_secretsmanager_secret" "dockerhub" {
  name        = "discord/dockerhub"
  description = "Docker Hub credentials (username/password) used by CodeBuild"
  tags        = local.common_tags
}

# Create a placeholder secret version — update it manually or via CLI after apply.
resource "aws_secretsmanager_secret_version" "dockerhub_version" {
  secret_id     = aws_secretsmanager_secret.dockerhub.id
  secret_string = jsonencode({
    username = "CHANGE_ME",
    password = "CHANGE_ME"
  })
}
