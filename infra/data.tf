data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    # Use a conservative default (Amazon Linux 2) for broader compatibility in mock runs.
    # If you prefer Amazon Linux 2023 / arm64 for t4g, change this to the relevant pattern.
    values = ["amzn2-ami-hvm-2.0.*-x86_64*", "amzn2-ami-hvm-2.0.*-aarch64*"]
  }
}

data "aws_availability_zones" "available" {}

data "aws_region" "current" {}

data "aws_caller_identity" "current" {}
