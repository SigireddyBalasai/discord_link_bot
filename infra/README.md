# Terraform infra for Discord Link Bot

This directory contains Terraform configuration to provision a minimal EC2-based environment for running the Discord bot in Docker, with EBS-backed persistence and CodeDeploy-based CI/CD.

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

4. Plan & apply:

```bash
terraform plan -var="key_name=your-key-name"
terraform apply -var="key_name=your-key-name" -auto-approve

You can pass `common_tags` to ensure tag consistency across the infrastructure. Example:

```bash
terraform plan -var='common_tags={owner="your-name",environment="dev"}' \
	-var='key_name=your-key-name'
terraform apply -var='common_tags={owner="your-name",environment="dev"}' \
	-var='key_name=your-key-name' -auto-approve
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
 - To deploy locally, you do not need remote workflows. Set the following locally (or in `.env`): `AWS_REGION`, `ECR_REPO`, `S3_BUCKET`, `CODEDEPLOY_APP`, `CODEDEPLOY_GROUP` and ensure `aws` + `docker` are available.

Local deploy with git hook
-------------------------

The repo includes a git pre-push hook template in `.githooks/pre-push` that calls `scripts/local_deploy.sh` to build, tag, push, upload the bundle, and trigger a CodeDeploy deployment. To enable:

1. Copy hooks into the repo's `.git/hooks`: 

```bash
cp .githooks/* .git/hooks/
chmod +x .git/hooks/*
```

2. (Optional) Or set git hooks path globally: 

```bash
git config core.hooksPath .githooks
```

3. Configure `.env` or export env vars used by `scripts/local_deploy.sh`:

```
AWS_REGION=ap-south-1
ECR_REPO=discord-link-bot
S3_BUCKET=discord-bot-deploy-471112640567
CODEDEPLOY_APP=discord-bot-app
CODEDEPLOY_GROUP=discord-bot-deployment-group
```

Now `git push` will build the Docker image, push it to ECR, and create a CodeDeploy deployment that deploys the bundle to your EC2 instance.

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
