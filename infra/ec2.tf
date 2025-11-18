resource "aws_security_group" "discord_bot" {
  name        = "discord-bot-sg"
  description = "Allow SSH and basic outbound for the bot"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {"Name" = "discord-bot-sg"})
}

resource "aws_instance" "discord_bot" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = var.key_name != "" ? var.key_name : null
  subnet_id              = element(module.vpc.public_subnets, 0)
  vpc_security_group_ids = [aws_security_group.discord_bot.id]

  iam_instance_profile = aws_iam_instance_profile.ec2_instance.name

  # Merge with global tags
  tags = merge(local.common_tags, {"Name" = "discord-bot-instance", "CodeDeployEnv" = "discord-bot"})

  user_data = templatefile("./userdata.tpl", {aws_region = var.aws_region})
}

resource "aws_ebs_volume" "discord_data" {
  availability_zone = element(data.aws_availability_zones.available.names, 0)
  size              = 5
  type              = "gp3"
  # Merge with global tags
  tags = merge(local.common_tags, {"Name" = "discord-bot-ebs"})
}

resource "aws_volume_attachment" "discord_data_attachment" {
  device_name = "/dev/sdh"
  volume_id   = aws_ebs_volume.discord_data.id
  instance_id = aws_instance.discord_bot.id
  skip_destroy = false
}
