 
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name = "name"
    values = var.ami_family == "amzn2023" ? ["amzn2023-ami-*-${local.ami_arch_name}*"] : ["amzn2-ami-hvm-*-${local.ami_arch_name}*"]
  }

  filter {
    name   = "architecture"
    values = [local.ami_arch_filter]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}


locals {
  ami_arch_name = var.ami_architecture == "aarch64" ? "arm64" : var.ami_architecture
  ami_arch_filter = var.ami_architecture == "aarch64" ? "arm64" : var.ami_architecture
  effective_ami_id = var.ami_id != "" ? var.ami_id : data.aws_ami.amazon_linux.id
}
data "aws_availability_zones" "available" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}
