#!/bin/bash

# AWS ECS Deployment Script for SuperMemory MCP Server
# This script deploys the SuperMemory server to AWS ECS with ALB

set -e

# Configuration
CLUSTER_NAME="supermemory-cluster"
SERVICE_NAME="supermemory-service" 
TASK_DEFINITION="supermemory-task"
IMAGE_NAME="supermemory-mcp"
AWS_REGION="${AWS_REGION:-us-west-2}"
VPC_ID="${VPC_ID:-}"  # Set your VPC ID
SUBNET_IDS="${SUBNET_IDS:-}"  # Set your subnet IDs (comma-separated)
SECURITY_GROUP_ID="${SECURITY_GROUP_ID:-}"  # Set your security group ID

echo "🚀 Deploying SuperMemory MCP Server to AWS ECS..."

# Check required environment variables
if [ -z "$VPC_ID" ] || [ -z "$SUBNET_IDS" ] || [ -z "$SECURITY_GROUP_ID" ]; then
    echo "❌ Please set VPC_ID, SUBNET_IDS, and SECURITY_GROUP_ID environment variables"
    echo "Example:"
    echo "  export VPC_ID=vpc-xxxxxxxx"
    echo "  export SUBNET_IDS=subnet-xxxxxxxx,subnet-yyyyyyyy"
    echo "  export SECURITY_GROUP_ID=sg-xxxxxxxx"
    exit 1
fi

# Step 1: Build and push Docker image to ECR
echo "📦 Building and pushing Docker image..."

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}"

# Create ECR repository if it doesn't exist
aws ecr describe-repositories --repository-names ${IMAGE_NAME} --region ${AWS_REGION} || \
aws ecr create-repository --repository-name ${IMAGE_NAME} --region ${AWS_REGION}

# Get login token and login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REPO}

# Build and tag image
docker build -t ${IMAGE_NAME} .
docker tag ${IMAGE_NAME}:latest ${ECR_REPO}:latest

# Push image
docker push ${ECR_REPO}:latest

echo "✅ Image pushed to ${ECR_REPO}:latest"

# Step 2: Create CloudWatch log group
aws logs create-log-group --log-group-name "/ecs/supermemory" --region ${AWS_REGION} || echo "Log group already exists"

# Step 3: Deploy using CloudFormation
echo "🏗️  Deploying infrastructure with CloudFormation..."

aws cloudformation deploy \
    --template-file cloudformation-template.json \
    --stack-name supermemory-stack \
    --parameter-overrides \
        VpcId=${VPC_ID} \
        SubnetIds=${SUBNET_IDS} \
        ImageUri=${ECR_REPO}:latest \
    --capabilities CAPABILITY_IAM \
    --region ${AWS_REGION}

echo "🎉 Deployment complete!"

# Get load balancer DNS
LB_DNS=$(aws cloudformation describe-stacks \
    --stack-name supermemory-stack \
    --query "Stacks[0].Outputs[?OutputKey=='LoadBalancerDNS'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

echo "📊 SuperMemory MCP Server is available at: http://${LB_DNS}"
echo "🩺 Health check: http://${LB_DNS}/health"

echo "📝 Monitor deployment:"
echo "   aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME} --region ${AWS_REGION}"
echo "   aws logs tail /ecs/supermemory --follow --region ${AWS_REGION}"
