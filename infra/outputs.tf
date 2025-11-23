output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.discord_bot.public_ip
}


output "ssh_private_key_pem" {
  value     = tls_private_key.discord_ssh.private_key_pem
  sensitive = true
}

output "ssh_keyfile_path" {
  value       = local_file.ssh_keyfile.filename
  description = "Local path to the generated private key file (sensitive)."
  sensitive   = true
}

output "codedeploy_app" {
  value = aws_codedeploy_app.discord_bot_app.name
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.discord_bot_table.name
  description = "Name of the DynamoDB table"
}

output "s3_bucket" {
  value       = var.bundle_s3_bucket
  description = "S3 bucket to upload CodeDeploy bundles (create outside Terraform or set via var)"
}

output "ecr_repo_uri" {
  value       = aws_ecr_repository.discord.repository_url
  description = "ECR repository URI"
}

output "ecr_repo_name" {
  value       = aws_ecr_repository.discord.name
  description = "ECR repository name"
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
