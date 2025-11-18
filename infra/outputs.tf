output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.discord_bot.public_ip
}

output "ssh_cmd" {
  value = var.key_name != "" ? "ssh -i <path-to-key> ec2-user@${aws_instance.discord_bot.public_ip}" : "ssh ec2-user@${aws_instance.discord_bot.public_ip}"
}

output "codedeploy_app" {
  value = aws_codedeploy_app.discord_bot_app.name
}

output "s3_bucket" {
  value = var.bundle_s3_bucket
  description = "S3 bucket to upload CodeDeploy bundles (create outside Terraform or set via var)"
}

output "ecr_repo_uri" {
  value       = var.ecr_repo != "" ? aws_ecr_repository.discord[0].repository_url : ""
  description = "ECR repository URI (empty if ecr_repo var not set)"
}

output "codecommit_clone_url_http" {
  value       = var.codecommit_name != "" ? aws_codecommit_repository.discord[0].clone_url_http : ""
  description = "HTTP clone URL for CodeCommit (empty if not created)"
}

output "codecommit_clone_url_ssh" {
  value       = var.codecommit_name != "" ? aws_codecommit_repository.discord[0].clone_url_ssh : ""
  description = "SSH clone URL for CodeCommit (empty if not created)"
}

output "codebuild_project" {
  value       = aws_codebuild_project.discord_build[0].name
  description = "CodeBuild project name (if pipeline enabled)"
}

output "codepipeline_name" {
  value       = aws_codepipeline.discord_pipeline[0].name
  description = "CodePipeline name (if enabled)"
}
