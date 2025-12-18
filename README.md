# Discord Link Bot

A Discord bot that monitors and forwards links from configured channels, with automated AWS infrastructure deployment using Terraform and CI/CD via CodePipeline.

## Features

- 🔗 **Link Monitoring**: Automatically detects and categorizes links (YouTube, Twitter, Twitch, GitHub, etc.)
- 📤 **Smart Forwarding**: Routes links to appropriate channels based on configurable ACLs
- ⚙️ **Slash Commands**: Full Discord slash command support for easy configuration
- 🚀 **Automated Deployment**: Push-to-deploy with CodeCommit → CodeBuild → CodeDeploy
- 📊 **Real-time Monitoring**: Watch your deployment progress right in your terminal
- 🏗️ **Infrastructure as Code**: Complete AWS infrastructure managed with Terraform

## Quick Start

### Prerequisites

- Python 3.13+
- Docker (for local development)
- AWS CLI configured
- Terraform >= 1.4.0
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd discord_link_bot
   ```

2. **Set up environment:**
   ```bash
   # Create .env file
   echo "DISCORD_TOKEN=your_discord_token_here" > .env
   ```

3. **Run with Docker:**
   ```bash
   docker build -t discord-link-bot .
   docker run --env-file .env discord-link-bot
   ```

   Or with uv:
   ```bash
   uv sync
   uv run python -m main
   ```

### Production Deployment

1. **Configure Terraform:**
   ```bash
   cd infra
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

2. **Deploy infrastructure:**
   ```bash
   terraform init
   terraform apply
   ```

3. **Set up CodeCommit remote:**
   ```bash
   # Get the CodeCommit URL
   CODECOMMIT_URL=$(terraform output -raw codecommit_clone_url_http)
   
   # Add remote
   git remote add codecommit $CODECOMMIT_URL
   ```

4. **Deploy and watch:**
   ```bash
   ./scripts/deploy-and-watch.sh "Initial deployment"
   ```

   This will:
   - Commit your changes
   - Push to CodeCommit
   - Monitor the pipeline execution in real-time
   - Show you when deployment completes

## Commands

| Command | Description |
|---------|-------------|
| `/ping` | Check bot latency |
| `/stats` | Show bot statistics (servers, users, latency) |
| `/invite` | Get the bot invite link |
| `/support` | Get support information |
| `/add_link_channel` | Add or configure a channel for link forwarding |
| `/remove_link_channel` | Remove a channel from link forwarding |
| `/list_link_channels` | List configured channels and their filters |
| `/set_link_filter` | Enable/disable specific link types for a channel |
| `/quick_link_setup` | One-step setup for a channel to receive all link types |

## Architecture

### AWS Infrastructure

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│ CodeCommit  │─────▶│  CodeBuild   │─────▶│ CodeDeploy  │
│  (Source)   │      │   (Build)    │      │   (Deploy)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────┐           ┌──────────┐
                     │   ECR    │           │   EC2    │
                     │ (Images) │           │ (Runtime)│
                     └──────────┘           └──────────┘
                                                  │
                                                  ▼
                                           ┌──────────┐
                                           │ DynamoDB │
                                           │  (Data)  │
                                           └──────────┘
```

**Resources Created:**
- VPC with 2 public subnets
- EC2 instance (t4g.nano) running Docker
- DynamoDB table for bot data
- ECR repository for Docker images
- CodeCommit repository for source code
- CodePipeline for automated CI/CD
- CodeBuild for building Docker images
- CodeDeploy for deploying to EC2
- S3 bucket for deployment artifacts
- CloudWatch log groups
- IAM roles and security groups

### Deployment Flow

1. **Push to CodeCommit** → EventBridge triggers pipeline
2. **CodeBuild** → Builds Docker image, pushes to ECR, creates deployment bundle
3. **CodeDeploy** → Pulls image from ECR, deploys to EC2
4. **EC2** → Runs bot container with CloudWatch logging

## Development

### Project Structure

```
discord_link_bot/
├── main.py                 # Bot entry point
├── cogs/                   # Command modules
│   ├── help.py            # Help command
│   ├── link_manager.py    # Link channel management
│   └── link_monitor.py    # Link detection and forwarding
├── core/                   # Core utilities
│   ├── bot_setup.py       # Bot initialization
│   ├── db/                # Database layer
│   └── logging_setup.py   # Logging configuration
├── infra/                  # Terraform infrastructure
│   ├── main.tf
│   ├── variables.tf
│   └── *.tf               # Other Terraform files
├── scripts/                # Helper scripts
│   └── deploy-and-watch.sh # Deploy and monitor script
├── Dockerfile              # Multi-stage Docker build
├── buildspec.yml           # CodeBuild configuration
├── appspec.yml             # CodeDeploy configuration
└── pyproject.toml          # Python dependencies (uv)
```

### Docker Build

The project uses a multi-stage Docker build with `uv` for dependency management:

**Build locally:**
```bash
DOCKER_BUILDKIT=1 docker build -t discord-link-bot:local .
```

**Run locally:**
```bash
docker run --env-file .env discord-link-bot:local
```

**Key features:**
- Alpine-based for small image size (~50MB)
- Multi-stage build (builder + runtime)
- BuildKit cache mounts for faster builds
- Compiled bytecode for faster startup
- No secrets in image (passed at runtime)

See [Docker Best Practices](#docker-best-practices) for more details.

### Environment Variables

**Required:**
- `DISCORD_TOKEN`: Your Discord bot token

**Optional:**
- `DYNAMODB_TABLE_NAME`: DynamoDB table name (auto-configured in production)
- `AWS_REGION`: AWS region (auto-configured in production)

**Production:** Token is stored in AWS Systems Manager Parameter Store and automatically retrieved by the EC2 instance.

**Local Development:** Create a `.env` file with your token.

## Deployment

### Automated Deployment with Git Hooks

This project uses Git hooks to automate the entire deployment workflow. Just use normal Git commands!

**Simple deployment:**
```bash
git push codecommit main
```

That's it! The Git hooks automatically:
1. ✅ Validate your code (pre-push hook)
2. 🚀 Push to CodeCommit
3. 📊 Monitor pipeline execution (post-push hook)
4. ✅ Notify you when deployment completes

**What happens automatically:**

**Pre-Push Validation:**
- Checks Python syntax
- Validates Terraform configuration
- Scans for secrets in code
- Validates Docker build
- Blocks push if any check fails

**Post-Push Monitoring:**
- Waits for pipeline to start
- Shows real-time status of each stage
- Displays success/failure with colored output
- Provides AWS Console links for debugging

**Example workflow:**
```bash
# Make changes
vim main.py

# Commit
git commit -m "feat: add new command"

# Deploy (hooks handle everything)
git push codecommit main
```

**Output:**
```
🔍 Pre-Push Validation
✓ Python syntax valid
✓ No secrets detected
✓ All pre-push checks passed!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 CodePipeline Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline: discord-bot-pipeline
Execution: abc123-def456

  ✓ Source: Succeeded
  ⏳ Build: InProgress
  ○ Deploy: Pending
```

### Skip Validation (Not Recommended)

If you need to bypass pre-push validation:
```bash
git push --no-verify codecommit main
```

### Git Hooks Features

The project includes 6 powerful Git hooks:

1. **pre-commit** - Formats, lints, and validates code before commit
2. **pre-push** - Validates code before push
3. **post-push** - Monitors pipeline execution
4. **post-commit** - Shows commit info and push reminders
5. **prepare-commit-msg** - Adds commit templates
6. **post-checkout** - Detects dependency changes

See `.git/hooks/README.md` for detailed documentation.

### Monitoring Deployments

**View pipeline status:**
```bash
aws codepipeline get-pipeline-state --name $(terraform -chdir=infra output -raw codepipeline_name)
```

**View build logs:**
```bash
aws logs tail /aws/codebuild/$(terraform -chdir=infra output -raw codebuild_project) --follow
```

**View bot logs:**
```bash
aws logs tail /<bot_group>/<bot_name>/logs --follow
```

## Infrastructure Management

### Terraform Configuration

**Key variables** (in `infra/terraform.tfvars`):

```hcl
bot_name              = "discord-bot"
bot_group             = "default"
aws_region            = "us-east-1"
discord_token         = "your-token-here"
instance_type         = "t4g.nano"
ami_architecture      = "aarch64"
allowed_ssh_cidr      = "your.ip.address/32"  # Restrict for production!
allow_ssh_anywhere    = false                  # Set to false for production
root_volume_encrypted = true
block_public_s3       = true
run_iac_scans         = true
```

### State Management

This project uses **local Terraform state**. The state file is git-ignored and contains sensitive information.

**Important:**
- Keep `terraform.tfstate` backed up securely
- Never commit state files to version control
- For team environments, coordinate Terraform runs to avoid conflicts

### Security Best Practices

✅ **Implemented:**
- EC2 root volume encryption
- IMDSv2 required (metadata protection)
- S3 server-side encryption
- S3 public access blocked
- ECR image scanning on push
- Least-privilege IAM roles
- SSM Parameter Store for secrets
- CloudWatch logging enabled

🔒 **Production Checklist:**
- [ ] Backup `terraform.tfstate` securely
- [ ] Restrict `allowed_ssh_cidr` to your IP/VPN
- [ ] Set `allow_ssh_anywhere = false`
- [ ] Use SSM Session Manager instead of SSH
- [ ] Enable `prevent_destroy = true` for critical resources
- [ ] Configure KMS key for SSM encryption
- [ ] Review IAM policies
- [ ] Set up CloudWatch alarms
- [ ] Enable AWS CloudTrail
- [ ] Configure DynamoDB backups

### Accessing EC2 Instance

**Recommended: SSM Session Manager** (no SSH port required)
```bash
aws ssm start-session --target <instance-id>
```

**Alternative: SSH**
```bash
SSH_KEY=$(terraform -chdir=infra output -raw ssh_keyfile_path)
INSTANCE_IP=$(terraform -chdir=infra output -raw public_ip)
ssh -i $SSH_KEY ec2-user@$INSTANCE_IP
```

### Cost Optimization

**Current configuration:**
- EC2: t4g.nano (ARM) ~$3/month
- CodeBuild: BUILD_GENERAL1_SMALL (ARM)
- DynamoDB: Pay-per-request (no idle costs)
- S3: Lifecycle policies expire old artifacts
- CloudWatch: 7-day log retention

**Estimated monthly cost:** $5-10 for low-traffic bot

## Docker Best Practices

### Multi-Stage Build

The Dockerfile uses a multi-stage build to keep the final image small:

1. **Builder stage**: Installs `uv` and dependencies
2. **Runtime stage**: Copies only `.venv` and application code

### BuildKit Cache

For faster builds, use BuildKit cache mounts:

```bash
DOCKER_BUILDKIT=1 docker build \
  --cache-from discord-link-bot:latest \
  -t discord-link-bot:latest .
```

### Registry Cache (CI)

CodeBuild uses ECR as a registry cache to speed up builds:

```bash
# In buildspec.yml
docker buildx build \
  --cache-from type=registry,ref=$ECR_REPO:buildcache \
  --cache-to type=registry,ref=$ECR_REPO:buildcache,mode=max \
  -t $ECR_REPO:latest .
```

### Security

- ❌ Never put secrets in Dockerfile
- ✅ Pass secrets at runtime via environment variables
- ✅ Use Docker secrets for production
- ✅ Pin base image versions for reproducibility
- ✅ Scan images with ECR image scanning

### Troubleshooting

**Build fails on Alpine:**
```bash
# Add build dependencies to Dockerfile builder stage
RUN apk add --no-cache build-base libffi-dev openssl-dev
```

**Missing uv.lock:**
```bash
uv lock
```

**Slow builds:**
- Enable BuildKit: `DOCKER_BUILDKIT=1`
- Use cache mounts (already configured)
- Use registry cache in CI (already configured)

## Troubleshooting

### Pipeline Failures

**Check CodeBuild logs:**
```bash
aws logs tail /aws/codebuild/$(terraform -chdir=infra output -raw codebuild_project) --follow
```

**Check CodeDeploy status:**
```bash
aws deploy list-deployments \
  --application-name $(terraform -chdir=infra output codedeploy_app) \
  --deployment-group-name <deployment-group-name>
```

### Bot Not Starting

**SSH into EC2 and check:**
```bash
# Check running containers
docker ps -a

# View container logs
docker logs <container-name>

# Check CodeDeploy agent
sudo service codedeploy-agent status
sudo tail -f /var/log/aws/codedeploy-agent/codedeploy-agent.log
```

### Database Issues

**Check DynamoDB table:**
```bash
aws dynamodb describe-table \
  --table-name $(terraform -chdir=infra output -raw dynamodb_table_name)
```

### Missing Dependencies

**Install jq (required for deploy-and-watch script):**
```bash
# Ubuntu/Debian
sudo apt install jq

# macOS
brew install jq

# Amazon Linux
sudo yum install jq
```

## Multi-Bot Support

This infrastructure supports deploying multiple Discord bots. See `infra/README-multi-bot.md` for detailed instructions on:

- Organizing bots into groups
- Sharing infrastructure resources
- Cost optimization strategies
- Per-bot vs shared resources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with Docker
5. Submit a pull request

## License

[Your License Here]

## Support

- **Issues**: Open an issue on GitHub
- **Discord**: Use `/support` command in your server
- **Documentation**: See `infra/README.md` for infrastructure details

## Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Dependency management with [uv](https://github.com/astral-sh/uv)
- Infrastructure on AWS
- Deployed with Terraform
