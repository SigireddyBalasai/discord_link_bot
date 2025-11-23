#!/bin/bash
set -e

# Install CodeDeploy agent
yum update -y
yum install -y ruby wget
cd /home/ec2-user
wget https://aws-codedeploy-us-east-1.s3.us-east-1.amazonaws.com/latest/install
chmod +x ./install
./install auto
systemctl enable codedeploy-agent
systemctl start codedeploy-agent

# Install Docker
yum install -y docker
systemctl enable docker
systemctl start docker

# Run a simple docker container on start to make sure everything is OK
# The container will later be stopped/started by CodeDeploy scripts.
if [ ! -f /usr/local/bin/run-discord-bot ]; then
  cat >/usr/local/bin/run-discord-bot <<'EOF'
#!/bin/bash
# This script expects a Docker image named discord-bot:latest
docker rm -f discord-bot || true
# Retrieve AWS account ID
aws_account_id=$(aws sts get-caller-identity --query Account --output text)
# Authenticate to ECR and pull the latest image
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com

# Pull the image from ECR
docker pull ${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/discord-bot:latest

# Run the bot container
docker run -d --name discord-bot \
  --restart unless-stopped \
  -e DYNAMODB_TABLE_NAME=${dynamodb_table_name} \
  --log-driver awslogs \
  --log-opt awslogs-region=${aws_region} \
  --log-opt awslogs-group=/discord-bot/logs \
  ${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com/discord-bot:latest
EOF
  chmod +x /usr/local/bin/run-discord-bot
fi


# Ensure cloudwatch log group exists - optional
# The AWS CLI must be configured or running under instance profile
/usr/local/bin/run-discord-bot || true
