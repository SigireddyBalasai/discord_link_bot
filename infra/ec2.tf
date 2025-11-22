resource "aws_security_group" "discord_bot" {
  name        = "${local.name_prefix}-sg"
  description = "Allow SSH and basic outbound for the bot"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, { "Name" = "${local.name_prefix}-sg" })
}

resource "aws_instance" "discord_bot" {
  ami                    = local.effective_ami_id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.discord_ssh.key_name
  subnet_id              = element(module.vpc.public_subnets, 0)
  vpc_security_group_ids = [aws_security_group.discord_bot.id]
  associate_public_ip_address = true

  iam_instance_profile = aws_iam_instance_profile.ec2_instance.name

  monitoring = true

  root_block_device {
    encrypted = var.root_volume_encrypted
  }


  tags = merge(local.tags, { "Name" = "${local.name_prefix}-instance", "CodeDeployEnv" = local.name_prefix })

  user_data = templatefile("./userdata.tpl", { aws_region = var.aws_region })
}

resource "aws_ebs_volume" "discord_data" {
  availability_zone = element(data.aws_availability_zones.available.names, 0)
  size              = var.ebs_size
  type              = var.ebs_type
  encrypted         = var.ebs_encrypted

  lifecycle {
    prevent_destroy = true
  }

  tags = merge(local.tags, { "Name" = "${local.name_prefix}-ebs" })
}

resource "aws_volume_attachment" "discord_data_attachment" {
  device_name  = "/dev/sdh"
  volume_id    = aws_ebs_volume.discord_data.id
  instance_id  = aws_instance.discord_bot.id
  skip_destroy = false
}

# Remove manual snapshot, use AWS Backup for automated retention
# resource "aws_ebs_snapshot" "discord_data_backup" {
#   volume_id = aws_ebs_volume.discord_data.id
#   tags = merge(local.tags, { "Name" = "${local.name_prefix}-ebs-snapshot" })
# }

resource "aws_backup_vault" "discord_backup_vault" {
  name = "${local.name_prefix}-backup-vault"
  tags = local.tags
}

resource "aws_backup_plan" "discord_ebs_backup_plan" {
  name = "${local.name_prefix}-ebs-backup-plan"

  rule {
    rule_name         = "daily_ebs_backup"
    target_vault_name = aws_backup_vault.discord_backup_vault.name
    schedule          = "cron(0 5 ? * * *)"  # Daily at 5 AM UTC

    lifecycle {
      delete_after = 7
    }
  }

  tags = local.tags
}

resource "aws_backup_selection" "discord_ebs_selection" {
  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "${local.name_prefix}-ebs-selection"
  plan_id      = aws_backup_plan.discord_ebs_backup_plan.id

  resources = [
    aws_ebs_volume.discord_data.arn
  ]
}

resource "aws_iam_role" "backup_role" {
  name = "${local.name_prefix}-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backup_policy" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}
