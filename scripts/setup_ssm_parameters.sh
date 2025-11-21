#!/bin/bash
set -e

# Script to set up SSM parameters for the Discord bot
# Usage: ./scripts/setup_ssm_parameters.sh <bot_name> <discord_token>

if [ $# -ne 2 ]; then
    echo "Usage: $0 <bot_name> <discord_token>"
    echo "Example: $0 discord-bot YOUR_DISCORD_TOKEN_HERE"
    exit 1
fi

BOT_NAME=$1
DISCORD_TOKEN=$2
AWS_REGION=${AWS_REGION:-us-east-1}

echo "Setting up SSM parameters for bot: ${BOT_NAME}"
echo "AWS Region: ${AWS_REGION}"

# Create the SSM parameter
PARAMETER_NAME="/${BOT_NAME}/DISCORD_TOKEN"

echo "Creating SSM parameter: ${PARAMETER_NAME}"
aws ssm put-parameter \
    --name "${PARAMETER_NAME}" \
    --value "${DISCORD_TOKEN}" \
    --type "SecureString" \
    --description "Discord bot token for ${BOT_NAME}" \
    --region "${AWS_REGION}" \
    --overwrite

if [ $? -eq 0 ]; then
    echo "✅ Successfully created SSM parameter: ${PARAMETER_NAME}"
    echo ""
    echo "To verify the parameter was created:"
    echo "aws ssm get-parameter --name \"${PARAMETER_NAME}\" --region ${AWS_REGION}"
    echo ""
    echo "To update the token later:"
    echo "aws ssm put-parameter --name \"${PARAMETER_NAME}\" --value \"NEW_TOKEN\" --overwrite --region ${AWS_REGION}"
else
    echo "❌ Failed to create SSM parameter"
    exit 1
fi