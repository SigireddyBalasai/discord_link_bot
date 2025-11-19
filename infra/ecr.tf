resource "aws_ecr_repository" "discord" {
  count = var.ecr_repo != "" ? 1 : 0

  name = var.ecr_repo
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = true
  }
  encryption_configuration {
    encryption_type = "AES256"
  }

  force_delete = var.ecr_force_delete

  tags = local.common_tags
}

resource "aws_ecr_repository" "base_images" {
  name                 = "discord-base-images"
  image_tag_mutability = "MUTABLE"
  image_scanning_configuration {
    scan_on_push = false
  }
  tags = local.common_tags
}
