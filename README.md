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
- Commands: `/ping`, `/stats`, `/invite`, `/support`, `/add_link_channel`, `/remove_link_channel`, `/list_link_channels`

## Commands

- `/ping`: Check bot latency
- `/stats`: Show bot statistics (servers, users, latency)
- `/invite`: Get the bot invite link
- `/support`: Get support information
- `/add_link_channel`: Add or configure a channel for link forwarding
- `/remove_link_channel`: Remove a channel from link forwarding
- `/list_link_channels`: List configured channels and their filters
- `/set_link_filter`: Enable/disable specific link types for a channel
- `/quick_link_setup`: One-step setup for a channel to receive all link types

## Continuous Deployment

Automated CI/CD (CodeCommit → CodeBuild → CodeDeploy) is enabled.

1. **Push to CodeCommit**:
   ```bash
   git push codecommit HEAD:refs/heads/main
   ```

2. **Pipeline Execution**:
   - Builds Docker image and pushes to ECR
   - Creates deployment artifact
   - Triggers CodeDeploy to update the EC2 instance

## Notes

- Protect secrets and never commit credentials.
- SSH access to the EC2 instance is enabled by default and open to `allowed_ssh_cidr` (default `0.0.0.0/0`); narrow this value for production.
