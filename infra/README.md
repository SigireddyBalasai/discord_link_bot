# Terraform infra for Discord Link Bot

This directory contains Terraform configuration to provision a minimal EC2-based environment for running the Discord bot in Docker, with EBS-backed persistence and CodeDeploy-based CI/CD.

**Note**: This infrastructure has been parameterized to support multiple Discord bots. See [README-multi-bot.md](README-multi-bot.md) for details on deploying multiple bots.

## Quick setup (safe defaults)

1. Install Terraform and AWS CLI.
2. Configure AWS credentials in your shell:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION=us-east-1
```

3. Initialize Terraform:

```bash
cd infra
terraform init
```

4. This repo uses CI/CD for builds and deployments; local build scripts were removed. To trigger a deployment run:

```
# push to the CodeCommit repo -> CodePipeline triggers the pipeline
git push codecommit HEAD:refs/heads/main
```

If you want to run containers locally for development, build and run Docker directly; use `$(terraform -chdir=infra output -raw ecr_repo_name)` to get the repo name if you need to push an image to ECR.

You can pass `common_tags` to ensure tag consistency across the infrastructure. Example:

```bash
terraform plan -var='common_tags={owner="your-name",environment="dev"}' \
	#terraform apply -var='common_tags={owner="your-name",environment="dev"}' -auto-approve
 
 Note: Terraform will create a key pair in AWS and write the private key to a local file for inspection and SSH access; the file is ignored by git and stored in your local machine for convenience. Use `terraform output -raw ssh_keyfile_path` to get the path after apply. CI still does the automated builds & deploys; local builds and local deploys remain unsupported.
```
```

## What gets created
- VPC with 2 public subnets (small sample by default)
- EC2 instance with Docker and CodeDeploy agent
- EBS volume attached to `/data` for persistent storage
- CloudWatch Log Group `/discord-bot/logs`
- S3 bucket for CodeDeploy bundles (unique per region)
 - (Optional) CodePipeline and CodeBuild to automate CI/CD from CodeCommit to CodeDeploy -- see below
- IAM roles for EC2 and CodeDeploy

## Notes & recommended secrets
 - `ECR_REPO` – the name of the ECR repo where either your local deploy or automated pipeline will push the image
 - `S3_BUCKET` – the S3 bucket created by Terraform will be the bundle destination; you can also set your own
 - Secure shell access: this project supports SSM Session Manager for remote management. SSH is enabled by default and `allowed_ssh_cidr` controls allowed source IPs.

SSM Session Manager
-------------------

The EC2 instance has the `AmazonSSMManagedInstanceCore` policy attached by default. To start a session from your machine use the AWS CLI:

```
aws ssm start-session --target <instance-id>
```

This avoids needing a public SSH port; recommended for production.

Production hardening checklist
-----------------------------

This repository is intended for production workloads. Below are recommended security and operational defaults we apply or suggest:

 - Use SSM Session Manager (recommended). SSH is enabled by default and accepts traffic from `allowed_ssh_cidr` (default 0.0.0.0/0); restrict this for production.

Provider configuration
----------------------

The Terraform AWS provider is now defined in `providers.tf`. This keeps provider setup separate from the high-level resource definitions in `main.tf`. For production: consider enabling `assume_role` with a specific `role_arn` or setting provider aliases for different accounts.
- EBS: additional data disk is encrypted by default (see `ebs_encrypted = true`) and root block device encryption is also enabled (`root_volume_encrypted = true`).
- S3: public access is blocked on the deployment artifact bucket (`block_public_s3 = true`).
- ECR: image scanning on push is enabled by default; ensure you push only trusted images.
 - ECR: image scanning on push is enabled by default; ensure you push only trusted images. The ECR repository is named `${local.name_prefix}-ecr_repository` by default — edit `infra/ecr.tf` to change the name if you need a custom repository.
 - ECR: image scanning on push is enabled by default; ensure you push only trusted images. The ECR repository is named `${local.name_prefix}-ecr_repository` by default — edit `infra/ecr.tf` to change the name if you need a custom repository.
- IAM: roles are scoped; review their least-privilege usage. Consider rotating keys and using AWS Organizations for centralized policy.
- CloudWatch: `monitoring = true` is enabled for the EC2 instance; enable log retention and alerting for critical logs.

If you want, I can add automated checks (e.g., local precommit or CI policy checks), configure SSM session logging to CloudWatch, or add a Optional `terraform plan` CI step to prevent accidental infra drift.

Deploying the app
-----------------

1. Enable the pipeline by setting `codecommit_name` in `infra/terraform.tfvars` (or pass `-var='codecommit_name=my-repo'` on the command line) and run `terraform apply` in the `infra` directory.

2. After `apply`, the ECR repository will be available as the default name — you can get it with:

```
terraform -chdir=infra output -raw ecr_repo_name
```

3. Push code to the CodeCommit repo configured by Terraform (or push to the remote `codecommit` if you set it). Example:

```
git push codecommit HEAD:refs/heads/main
```

This push triggers CodePipeline (Source → Build → Deploy). Alternatively, start the pipeline manually:

```
aws codepipeline start-pipeline-execution --name $(terraform -chdir=infra output -raw codepipeline_name)
```

4. The pipeline builds the Docker image, pushes it to the ECR repository, archives a CodeDeploy bundle to the S3 bucket, and then runs a CodeDeploy deployment to the EC2 instance. Use `aws codepipeline get-pipeline-state` and CodeBuild/CodeDeploy consoles to view logs and deployment status.

Advanced: SSH-over-SSM (no inbound port required)
------------------------------------------------

If you need to run your local SSH client against the instance, you can use SSM to forward a port locally. This avoids ever opening port 22 in the security group but still allows an SSH session using your existing SSH tools:

1. Start a port forwarding session (AWS CLI v2):

```
aws ssm start-session \
	--target i-0123456789abcdef0 \
	--document-name AWS-StartPortForwardingSession \
	--parameters '{"portNumber":["22"],"localPortNumber":["2022"]}'
```

2. In a different terminal, connect with SSH:

```
ssh -i /path/to/key -p 2022 ec2-user@localhost
```

This uses the SSM agent to forward remote port 22 through the SSM channel to your machine's port 2022. No inbound SSH (22) is required on security groups.

EC2 Instance Connect vs Session Manager
--------------------------------------

You can also use "EC2 Instance Connect" from the AWS Console to open a browser-based SSH terminal to an instance. However, EC2 Instance Connect still requires SSH traffic on port 22, so if your security group blocks SSH / 0.0.0.0/0 is not present, the Instance Connect option won't work. Session Manager works regardless of port 22.
 - The repository no longer supports local builds or deploys; use the CI pipeline for building and deploying images and artifacts.

Local builds and deployment via git hooks were removed — the pipeline is the supported way to build and deploy.

Automated CI/CD with CodePipeline
---------------------------------

Automated CI/CD is enabled by default: Terraform will create a CodeCommit (if specified), CodeBuild and CodePipeline (when `codecommit_name` is provided) to automatically build and deploy on pushes to `main`.

Example variables: instead of passing `-var` repeatedly on the CLI, use a tfvars file.

Create `infra/terraform.tfvars` or copy the example `infra/terraform.tfvars.example` and edit it:

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# edit terraform.tfvars to add your values
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars -auto-approve
```

The pipeline does the following:

- Source: CodeCommit (branch: main)
- Build: CodeBuild (runs `buildspec.yml`) — this builds the Docker image, pushes it to ECR, and packages an artifact (appspec + scripts) for the deploy stage.
- Deploy: CodeDeploy uses the build artifact to perform a standard CodeDeploy lifecycle (appspec.yml + hooks) on the EC2 instance.

CodeBuild triggers
------------------

This repository configures a full pipeline: CodeCommit (source) -> CodeBuild -> CodeDeploy (deploy). The pipeline is enabled by default and will automatically build and deploy on pushes to the `main` branch.

We removed the independent EventBridge CodeBuild trigger so builds run only as part of the pipeline (keeps behavior predictable and avoids duplicate builds). If you need an independent trigger in the future, we can reintroduce it.


Manual approval
---------------

The pipeline does not include a manual approval stage by default; everything is automated: pushes to `main` will be built by CodeBuild and deployed with CodeDeploy. If you want to re-introduce a manual approval stage, we can add a variable and reconfigure the pipeline.

When enabled, a `ManualApproval` action appears in CodePipeline and requires someone with appropriate permissions in the AWS Console to click `Approve` before CodeDeploy runs.

If you prefer another CI provider to run the build step instead of CodeBuild, remove the `codecommit` remote and configure your CI provider to build the Docker image and trigger CodeDeploy.

## Warnings
- This is a sample and intentionally minimal. Audit the IAM statements before using in production.
- Do not store Discord tokens in `Dockerfile` — use runtime environment variables or Secrets Manager.
