#!/bin/bash
set -e

BOT_NAME=${BOT_NAME:-discord-link-bot}

echo "Stopping Discord bot container..."
docker stop "$BOT_NAME" || true
docker rm "$BOT_NAME" || true

echo "Container stopped."