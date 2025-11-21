# Multi-Bot Deployment Guide

This infrastructure has been parameterized to support multiple Discord bots. Each bot can have its own isolated set of resources while sharing the same Terraform codebase.

## Deploying Multiple Bots

### Method 1: Separate Terraform State Files (Recommended)

1. **Create a directory for each bot:**
```bash
mkdir infra-bot1 infra-bot2
cp -r infra/* infra-bot1/
cp -r infra/* infra-bot2/
```

2. **Configure each bot:**
   - Edit `infra-bot1/terraform.tfvars`:
   ```hcl
   bot_name       = "bot1"
   codecommit_name = "discord-bot1-repo"
   aws_region      = "us-east-1"
   ```

   - Edit `infra-bot2/terraform.tfvars`:
   ```hcl
   bot_name       = "bot2"
   codecommit_name = "discord-bot2-repo"
   aws_region      = "us-east-1"
   ```

3. **Deploy each bot:**
```bash
cd infra-bot1
terraform init
terraform apply

cd ../infra-bot2
terraform init
terraform apply
```

### Method 2: Terraform Workspaces

1. **Use workspaces:**
```bash
cd infra
terraform workspace create bot1
terraform workspace select bot1

# Edit terraform.tfvars for bot1
terraform apply

terraform workspace create bot2
terraform workspace select bot2

# Edit terraform.tfvars for bot2
terraform apply
```

## Environment Variables

Each bot needs its own environment configuration:

- **DISCORD_TOKEN**: Unique Discord bot token for each bot
- **AWS_REGION**: AWS region (can be shared)
- **LOG_GROUP**: Automatically derived as `/{bot_name}/logs`

## Resource Naming

All resources are now prefixed with the `bot_name`:

- EC2 Instance: `{bot_name}-instance`
- ECR Repository: `{bot_name}-ecr_repository`
- S3 Bucket: `{bot_name}-codedeploy-bundles-{region}`
- Log Group: `/{bot_name}/logs`

## Cost Optimization

Multiple bots can share:
- VPC and networking
- NAT Gateway
- Basic infrastructure

Each bot gets its own:
- EC2 instance
- EBS volume
- ECR repository
- CI/CD pipeline (optional)

## Example Configuration

For a bot named "music-bot":

```hcl
bot_name       = "music-bot"
codecommit_name = "discord-music-bot"
aws_region      = "us-east-1"

tags = {
  ManagedBy = "Terraform"
  Project   = "music-bot"
  Owner     = "team-music"
}
```