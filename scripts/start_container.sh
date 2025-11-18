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

# Run container
docker run -d --name discord-bot \
  --restart unless-stopped \
  -v /data:/data \
  --log-driver awslogs \
  --log-opt awslogs-group=/discord-bot/logs \
  --log-opt awslogs-region=${REGION:-${AWS_REGION}} \
  ${image_name}

exit 0
