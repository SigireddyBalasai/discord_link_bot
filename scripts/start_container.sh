#!/bin/bash
set -e

echo "Starting Discord bot container..."

# Read the ECR repo name
ECR_REPO=$(cat /tmp/deploy/ECR_REPO)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_TAG=$(grep BRANCH /tmp/deploy/.deploy_meta | cut -d'=' -f2)
IMAGE_URI=$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/$ECR_REPO:$IMAGE_TAG

echo "Pulling image: $IMAGE_URI"
docker pull $IMAGE_URI

echo "Starting container..."
DISCORD_TOKEN=$(aws ssm get-parameter --name /discord-bot/discord-link-bot/discord_token --with-decryption --query Parameter.Value --output text --region us-east-1)
docker run -d --name discord-bot --restart unless-stopped -p 80:80 -e DISCORD_TOKEN="$DISCORD_TOKEN" $IMAGE_URI

echo "Container started."