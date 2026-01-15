#!/bin/bash
set -e

echo "Starting Discord bot container..."

BOT_GROUP=${BOT_GROUP:-discord-bot}
BOT_NAME=${BOT_NAME:-discord-link-bot}
REGION=${REGION:-us-east-1}

# Read the ECR repo name
ECR_REPO=$(cat /tmp/deploy/ECR_REPO)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$REGION")
IMAGE_TAG=$(grep BRANCH /tmp/deploy/.deploy_meta | cut -d'=' -f2)
IMAGE_URI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG

echo "Pulling image: $IMAGE_URI"
docker pull "$IMAGE_URI"

echo "Starting container..."
DISCORD_TOKEN=$(aws ssm get-parameter --name /$BOT_GROUP/$BOT_NAME/discord_token --with-decryption --query Parameter.Value --output text --region "$REGION" | tr -d '\n')
docker run -d --name "$BOT_NAME" --restart unless-stopped -p 80:80 -e DISCORD_TOKEN="$DISCORD_TOKEN" -e DYNAMODB_TABLE_NAME="$BOT_NAME-table" "$IMAGE_URI"

echo "Container started."