variable "aws_region" {
  description = "AWS region to create resources in"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.nano"
}

variable "key_name" {
  description = "Optional SSH key name for the EC2 instance"
  type        = string
  default     = ""
}

variable "bundle_s3_bucket" {
  description = "S3 bucket where CodeDeploy bundles are uploaded"
  type        = string
  default     = "" 
}

variable "ecr_repo" {
  description = "ECR repository name used by the EC2 instance to pull images"
  type        = string
  default     = ""
}

variable "ecr_force_delete" {
  description = "Whether Terraform will force delete the repository on destroy (true will delete even if images present)"
  type        = bool
  default     = true
}

variable "common_tags" {
  description = "Map of common tags applied to all AWS resources"
  type        = map(string)
  default     = {}
}

variable "dockerhub_username" {
  description = "Optional Docker Hub username to authenticate image pulls in CodeBuild. Leave empty to skip DockerHub auth."
  type        = string
  default     = ""
}

variable "dockerhub_password_secret_arn" {
  description = "Optional ARN of a Secrets Manager secret containing the Docker Hub password; used to inject DOCKERHUB_PASSWORD into CodeBuild (type SECRETS_MANAGER)."
  type        = string
  default     = ""
}

variable "codecommit_name" {
  description = "Optional CodeCommit repository name; leave blank to not create CodeCommit."
  type        = string
  default     = ""
}

/* Pipeline is always enabled for this project (CodeCommit → CodeBuild → CodeDeploy). */


/* NOTE: `enable_manual_approval` and `enable_codebuild_trigger` were removed: pipeline is fully automated.
   If you need manual approval in the future, add a variable and re-introduce the stage in `pipeline.tf`.
*/
