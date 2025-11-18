#!/bin/bash
set -e

# Create mount for EBS
# Wait for device then format & mount
DEVICE="/dev/sdh"
MOUNT_DIR="/data"

# Install docker and deps
yum update -y
amazon-linux-extras enable docker
yum install -y docker
systemctl enable --now docker

# Install CodeDeploy agent prereqs
yum install -y ruby wget
cd /tmp

# Install AWS CLI v2 (optional)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install || true

# Install CodeDeploy agent
CODENAME="codedeploy-agent"
# use the configured aws_region for CodeDeploy agent download
(cd /tmp && wget https://aws-codedeploy-${aws_region}.s3.amazonaws.com/latest/install)
chmod +x ./install
sudo ./install auto

mkdir -p $MOUNT_DIR

# Wait for device availability
for i in {1..30}; do
  if [ -e $DEVICE ]; then break; fi
  echo "waiting for $DEVICE"; sleep 2
done

if ! file -s $DEVICE | grep -q ext4; then
  mkfs -t ext4 $DEVICE || true
fi

mount $DEVICE $MOUNT_DIR || true

# Remount at boot
echo "$DEVICE $MOUNT_DIR ext4 defaults,nofail 0 2" >> /etc/fstab

# Run a simple docker container on start to make sure everything is OK
# The container will later be stopped/started by CodeDeploy scripts.
if [ ! -f /usr/local/bin/run-discord-bot ]; then
  cat >/usr/local/bin/run-discord-bot <<'EOF'
#!/bin/bash
# This script expects a Docker image named discord-bot:latest
docker rm -f discord-bot || true
# Run the bot with a volume for persistent storage
docker run -d --name discord-bot \
  --restart unless-stopped \
  -v /data:/data \
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
