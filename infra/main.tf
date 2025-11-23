terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }

  required_version = ">= 1.4.0"
}



locals {
  name_prefix = var.bot_name
  tags = merge({
    Project   = local.name_prefix,
    ManagedBy = "Terraform"
  }, var.tags)
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 4.0"

  name = "${local.name_prefix}-vpc"
  cidr = "10.2.0.0/16"

  azs                = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnets     = ["10.2.1.0/24", "10.2.2.0/24"]
  enable_nat_gateway = false
  single_nat_gateway = false

  tags = local.tags
}
