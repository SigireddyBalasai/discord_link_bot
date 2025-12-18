#!/bin/bash
set -e

echo "Stopping Discord bot container..."
docker stop discord-bot || true
docker rm discord-bot || true

echo "Container stopped."