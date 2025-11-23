resource "tls_private_key" "discord_ssh" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "discord_ssh" {
  key_name   = "${local.name_prefix}-ssh"
  public_key = tls_private_key.discord_ssh.public_key_openssh

  tags = local.tags
}

resource "local_file" "ssh_keyfile" {
  content         = tls_private_key.discord_ssh.private_key_pem
  filename        = "${path.module}/.ssh/${local.name_prefix}-ssh.pem"
  file_permission = "0600"
}


