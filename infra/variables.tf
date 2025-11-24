variable "aws_region" {
  description = "AWS region to create resources in"
  type        = string
  default     = "us-east-1"
}

variable "bot_name" {
  description = "Name of the bot (used for resource naming and identification)"
  type        = string
  default     = "discord-bot"
}

variable "ami_family" {
  description = "AMI family to use. Supported: 'amzn2' or 'amzn2023'"
  type        = string
  default     = "amzn2"
}

variable "ami_architecture" {
  description = "AMI architecture to use, e.g. 'x86_64' or 'aarch64'"
  type        = string
  default     = "aarch64"
}

variable "ami_id" {
  description = "Explicit AMI ID to use. If set, this overrides other selection methods."
  type        = string
  default     = ""
}



variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t4g.nano"
}


variable "allowed_ssh_cidr" {
  description = "CIDR allowed to SSH into the EC2 instance (default 0.0.0.0/0). WARNING: Set a narrower CIDR for production to improve security."
  type        = string
  default     = "0.0.0.0/0"

  validation {
    condition     = can(cidrhost(var.allowed_ssh_cidr, 0))
    error_message = "The allowed_ssh_cidr value must be a valid CIDR block."
  }
}

/* SSH access is always enabled; use `allowed_ssh_cidr` to restrict where SSH is accepted. */






variable "root_volume_encrypted" {
  description = "Whether the instance root block device should be encrypted."
  type        = bool
  default     = true
}

variable "block_public_s3" {
  description = "Block public access on S3 buckets created by Terraform"
  type        = bool
  default     = true
}

variable "run_iac_scans" {
  description = "Whether to run IaC security scans (tfsec, checkov) in CodeBuild. Default true for production."
  type        = bool
  default     = true
}

variable "bundle_s3_bucket" {
  description = "S3 bucket where CodeDeploy bundles are uploaded"
  type        = string
  default     = ""
}



variable "ecr_force_delete" {
  description = "Whether Terraform will force delete the repository on destroy (true will delete even if images present)"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Map of common tags applied to all AWS resources"
  type        = map(string)
  default     = {}
}



variable "codecommit_name" {
  description = "Optional CodeCommit repository name; leave blank to not create CodeCommit."
  type        = string
  default     = ""
}





