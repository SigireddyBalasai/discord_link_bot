#!/bin/bash
set -e

# Run a simple docker container on start to make sure everything is OK
# The container will later be stopped/started by CodeDeploy scripts.
if [ ! -f /usr/local/bin/run-discord-bot ]; then
  cat >/usr/local/bin/run-discord-bot <<'EOF'
#!/bin/bash
# This script expects a Docker image named discord-bot:latest
docker rm -f discord-bot || true
# Run the bot
docker run -d --name discord-bot \
  --restart unless-stopped \
  -e DYNAMODB_TABLE_NAME=${dynamodb_table_name} \
  --log-driver awslogs \
  --log-opt awslogs-region=${aws_region} \
  --log-opt awslogs-group=/discord-bot/logs \
  discord-bot:latest
EOF
  chmod +x /usr/local/bin/run-discord-bot
fi


# Ensure cloudwatch log group exists - optional
# The AWS CLI must be configured or running under instance profile
/usr/local/bin/run-discord-bot || true
