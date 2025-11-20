#!/bin/bash
set -e

# Pull latest image and start container
if [ -z "$ECR_REPO" ]; then
  echo "ECR_REPO not configured; trying local image"
  docker pull discord-bot:latest || true
  image_name="discord-bot:latest"
else
  REGION=$(curl -s 'http://169.254.169.254/latest/dynamic/instance-identity/document' | jq -r .region || echo "${AWS_REGION}")
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  image_name="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}:latest"
  docker pull ${image_name}
fi

# If ECR_REPO isn't supplied, try the terraform-managed repo name
if [ -z "$ECR_REPO" ]; then
  if command -v terraform >/dev/null 2>&1; then
    ECR_REPO=$(cd "$(dirname "$0")/.." && terraform -chdir=infra output -raw ecr_repo_name 2>/dev/null || true)
  fi
fi

# Run container
docker run -d --name discord-bot \
  --restart unless-stopped \
  -v /data:/data \
  --log-driver awslogs \
  --log-opt awslogs-group=/discord-bot/logs \
  --log-opt awslogs-region=${REGION:-${AWS_REGION}} \
  ${image_name}

exit 0
