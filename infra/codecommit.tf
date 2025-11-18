resource "aws_codecommit_repository" "discord" {
  count           = var.codecommit_name != "" ? 1 : 0
  repository_name = var.codecommit_name
  description     = "CodeCommit repository for Discord Link Bot"
  tags            = local.common_tags
}
