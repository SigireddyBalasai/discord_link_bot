Notes

- For CI, this repository uses AWS CodeCommit + CodeBuild + CodePipeline. If you prefer another system, you can implement equivalent steps to build the Docker image and call CodeDeploy.
# Discord Link Bot

This repo is set up to deploy the Discord bot to a single EC2 instance using CodeDeploy. All builds and deploys are handled through the CI pipeline; local deployment is not supported.

## Configuration

The bot requires the following environment variables:

- `DISCORD_TOKEN`: Your Discord bot token (required)

### Setting up Environment Variables

For **production deployment**, the bot retrieves the `DISCORD_TOKEN` from AWS Systems Manager Parameter Store:

1. **Set up the SSM parameter:**
   ```bash
   ./scripts/setup_ssm_parameters.sh discord-bot YOUR_DISCORD_TOKEN_HERE
   ```

2. **The deployment script automatically retrieves** the token from SSM parameter `/discord-bot/DISCORD_TOKEN`

For **local development**, create a `.env` file:
```bash
echo "DISCORD_TOKEN=your_discord_token_here" > .env
```

### Multi-Bot Support

This infrastructure supports multiple bots. For additional bots:

1. Update `infra/terraform.tfvars` with a new `bot_name`
2. Run `terraform apply` to create new resources
3. Set up SSM parameters: `./scripts/setup_ssm_parameters.sh <bot_name> <token>`
4. Deploy the bot code

See `infra/README-multi-bot.md` for detailed instructions.

## Features

- Monitors messages for links in configured channels
- Categorizes links (YouTube, Twitter, Twitch, GitHub, etc.)
- Forwards links to appropriate channels based on ACLs
- Commands: `/ping`, `/stats`, `/invite`, `/support`, `/add_channel`, `/remove_channel`, `/list_channels`

## Commands

- `/ping`: Check bot latency
- `/stats`: Show bot statistics (servers, users, latency)
- `/invite`: Get the bot invite link
- `/support`: Get support information
- `/add_channel`: Add a channel for link forwarding
- `/remove_channel`: Remove a channel from link forwarding
- `/list_channels`: List configured channels
```
ECR_REPO=$(terraform -chdir=infra output -raw ecr_repo_name)
S3_BUCKET=discord-bot-deploy-471112640567
CODEDEPLOY_APP=discord-bot-app
CODEDEPLOY_GROUP=discord-bot-deployment-group
```

4. Enable the git hook:

```bash
# Git hooks are intentionally not supported locally — the CI performs builds/deploys.
```

Local builds are not supported — use the CI pipeline for builds and deployments. SSH access to the EC2 instance is enabled by default and open to `allowed_ssh_cidr` (default `0.0.0.0/0`); narrow this value for production.

CodeCommit setup and mirror
---------------------------

We now use AWS CodeCommit as the primary remote for this repo. If you want to mirror the repository to AWS CodeCommit and push code there as well, you can run the setup script (or use it to switch to CodeCommit):

```bash
scripts/setup_codecommit.sh discord-link-bot
```

- Create a CodeCommit repo named `discord-link-bot` (if not exists)
- Configure the AWS CodeCommit credential helper for Git
- Add a Git remote called `codecommit` pointing at the AWS repo
This will:
- Create a CodeCommit repo named `discord-link-bot` (if not exists)
- Configure the AWS CodeCommit credential helper for Git
- Add a Git remote called `codecommit` pointing at the AWS repo

Continuous deployment (automated)
---------------------------------

Automated CI/CD (CodeCommit → CodeBuild → CodeDeploy) can be enabled by setting `codecommit_name` in `infra/terraform.tfvars` or passing it via `-var-file` to `terraform`. The Terraform configuration creates a default ECR repository named `${local.name_prefix}-ecr_repository`; if you want a custom name, edit `infra/ecr.tf`.

- Builds the Docker image and pushes it to ECR
- Produces a deployment artifact (appspec + scripts)
- Automatically triggers a CodeDeploy deployment using the artifact

This provides an automated push-to-deploy flow using CodeCommit → CodeBuild → CodeDeploy.
To make CodeCommit the canonical remote you push to (optional) you can run:

```bash
# rename the remote to origin (optional, sets CodeCommit as default remote)
git remote set-url origin $(terraform output -raw codecommit_clone_url_http)
```
- Create a CodeCommit repo named `discord-link-bot` (if not exists)
- Configure the AWS CodeCommit credential helper for Git
- Add a Git remote called `codecommit` pointing at the AWS repo

Push to CodeCommit with:

```bash
git push codecommit HEAD:refs/heads/main
```

If you renamed the CodeCommit remote to `origin` you can still use the pre-push hook — set `CODECOMMIT_REMOTE=origin` before pushing.

Note: for SSH clone/push, add your SSH public key to your IAM user in the AWS Console (or upload via CLI). Then change the remote to the SSH clone url shown by `terraform output codecommit_clone_url_ssh` (if using Terraform) or `aws codecommit get-repository ...`.

5. `git push` will trigger the pre-push hook that builds the docker image, pushes it to ECR, prepares the CodeDeploy bundle, uploads it to S3, and then triggers CodeDeploy.

Notes

- Protect secrets and never commit credentials.
- Protect secrets and never commit credentials.
