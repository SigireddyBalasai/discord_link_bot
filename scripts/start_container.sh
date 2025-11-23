#!/bin/bash
set -e

# Read ECR_REPO from file
if [ -f ECR_REPO ]; then
  ECR_REPO=$(cat ECR_REPO)
else
  ECR_REPO="discord-bot-ecr_repository"
fi

# Derive bot name from ECR repo (remove -ecr_repository suffix)
BOT_NAME=$(echo $ECR_REPO | sed 's/-ecr_repository$//')
CONTAINER_NAME=${CONTAINER_NAME:-$BOT_NAME}
LOG_GROUP=${LOG_GROUP:-/$BOT_NAME/logs}
AWS_REGION=${AWS_REGION:-us-east-1}

# Retrieve DISCORD_TOKEN from SSM Parameter Store
DISCORD_TOKEN_PARAM="/${BOT_NAME}/DISCORD_TOKEN"
echo "Retrieving DISCORD_TOKEN from SSM parameter: ${DISCORD_TOKEN_PARAM}"
DISCORD_TOKEN=$(aws ssm get-parameter --name "${DISCORD_TOKEN_PARAM}" --with-decryption --query Parameter.Value --output text --region $AWS_REGION 2>/dev/null)

if [ -z "$DISCORD_TOKEN" ] || [ "$DISCORD_TOKEN" = "None" ]; then
  echo "ERROR: Failed to retrieve DISCORD_TOKEN from SSM parameter ${DISCORD_TOKEN_PARAM}"
  echo "Make sure the parameter exists and the EC2 instance has permission to access it"
  exit 1
fi

echo "Successfully retrieved DISCORD_TOKEN from SSM"
if [ -z "$ECR_REPO" ]; then
  echo "ECR_REPO not configured; trying local image"
  docker pull discord-bot:latest || true
  image_name="discord-bot:latest"
else
  ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region $AWS_REGION)
  image_name="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/${ECR_REPO}:latest"
  docker pull ${image_name}
fi

# Run container
CONTAINER_NAME=${CONTAINER_NAME:-discord-bot}
LOG_GROUP=${LOG_GROUP:-/discord-bot/logs}
AWS_REGION=${AWS_REGION:-us-east-1}

docker run -d --name ${CONTAINER_NAME} \
  --network host \
  --restart unless-stopped \
  -v /data:/data \
  --log-driver awslogs \
  --log-opt awslogs-group=${LOG_GROUP} \
  --log-opt awslogs-region=${AWS_REGION} \
  -e DISCORD_TOKEN="${DISCORD_TOKEN}" \
  -e AWS_REGION="${AWS_REGION}" \
  -e DYNAMODB_TABLE_NAME="discord-bot-table" \
  -e DB_PATH="/data/bot_data.db" \
  ${image_name}

exit 0
