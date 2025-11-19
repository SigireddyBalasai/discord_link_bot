#!/usr/bin/env bash
# Local deploy script is intentionally retained for reference but local builds/deploys are unsupported.
exit 1

set -euo pipefail

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Validate required env vars
required=(AWS_REGION ECR_REPO S3_BUCKET CODEDEPLOY_APP CODEDEPLOY_GROUP)
for v in "${required[@]}"; do
  if [ -z "${!v:-}" ]; then
    echo "ERROR: required env var $v not set. Create .env or export them before running this script."
    exit 2
  fi
done

# If ECR_REPO isn't supplied, try to use the terraform-managed repo name
if [ -z "${ECR_REPO:-}" ]; then
  if command -v terraform >/dev/null 2>&1; then
    ECR_REPO=$(cd "$(dirname "$0")/.." && terraform -chdir=infra output -raw ecr_repo_name 2>/dev/null || true)
  fi
fi

# Determine account id
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

echo "Building Docker image: $ECR_REPO:latest"
docker build -t ${ECR_REPO}:latest .

# ensure ecr repo exists
echo "Checking ECR repository: $ECR_REPO"
if ! aws ecr describe-repositories --repository-names ${ECR_REPO} --region ${AWS_REGION} >/dev/null 2>&1; then
  echo "ECR repo doesn't exist; creating"
  aws ecr create-repository --repository-name ${ECR_REPO} --region ${AWS_REGION} >/dev/null
fi

# login & push image
echo "Logging in to ECR"
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "Tagging image as $ECR_URI:latest"
docker tag ${ECR_REPO}:latest ${ECR_URI}:latest

echo "Pushing image to ECR"
docker push ${ECR_URI}:latest

# Prepare CodeDeploy bundle
BUNDLE_DIR="deploy_bundle"
BUNDLE_NAME="bundle-$(date +%s).tar.gz"
rm -rf $BUNDLE_DIR
mkdir -p $BUNDLE_DIR

cp -r appspec.yml scripts/* $BUNDLE_DIR/ || true
# Add file containing ECR repo name so prebuilt scripts can read it
printf "%s" "${ECR_REPO}" > $BUNDLE_DIR/ECR_REPO

# Include optional other metadata (commit sha, branch)
GIT_SHA=$(git rev-parse --short HEAD)
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
cat > $BUNDLE_DIR/.deploy_meta <<EOF
BRANCH=${GIT_BRANCH}
SHA=${GIT_SHA}
ECR=${ECR_REPO}
EOF

# Create archive

tar -czf $BUNDLE_NAME -C $BUNDLE_DIR .

# Upload to S3
S3_KEY="deployments/${GIT_SHA}.tar.gz"
echo "Uploading $BUNDLE_NAME to s3://${S3_BUCKET}/${S3_KEY}"
aws s3 cp $BUNDLE_NAME s3://${S3_BUCKET}/${S3_KEY}

# Trigger CodeDeploy
echo "Creating CodeDeploy deployment"
DEP_ID=$(aws deploy create-deployment --application-name ${CODEDEPLOY_APP} --deployment-group-name ${CODEDEPLOY_GROUP} --s3-location bucket=${S3_BUCKET},key=${S3_KEY},bundleType=tgz --query deploymentId --output text)

echo "Deployment created: $DEP_ID"

# Optionally wait for deployment to finish
echo "Waiting for deployment to complete..."
aws deploy wait deployment-successful --deployment-id $DEP_ID

echo "Deployment $DEP_ID finished successfully"

# Cleanup
rm -rf $BUNDLE_DIR $BUNDLE_NAME

exit 0
