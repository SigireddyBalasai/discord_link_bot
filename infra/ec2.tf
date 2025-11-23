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

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    encrypted = var.root_volume_encrypted
  }


  tags = merge(local.tags, { "Name" = "${local.name_prefix}-instance", "CodeDeployEnv" = local.name_prefix })

  user_data = templatefile("./userdata.tpl", {
    aws_region          = var.aws_region
    dynamodb_table_name = aws_dynamodb_table.discord_bot_table.name
  })
}
