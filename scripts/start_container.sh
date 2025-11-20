#!/bin/bash
set -e

# Read ECR_REPO from file
if [ -f ECR_REPO ]; then
  ECR_REPO=$(cat ECR_REPO)
else
  ECR_REPO="discord-bot-ecr_repository"
fi

# Pull latest image and start container
if [ -z "$ECR_REPO" ]; then
  echo "ECR_REPO not configured; trying local image"
  docker pull discord-bot:latest || true
  image_name="discord-bot:latest"
else
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  image_name="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/${ECR_REPO}:latest"
  docker pull ${image_name}
fi

# Run container
docker run -d --name discord-bot \
  --restart unless-stopped \
  -v /data:/data \
  --log-driver awslogs \
  --log-opt awslogs-group=/discord-bot/logs \
  --log-opt awslogs-region=us-east-1 \
  ${image_name}

exit 0
