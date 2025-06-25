#!/bin/bash
# AWSNoc IA IA - Setup Script para EC2

set -e

# Variables from Terraform
DB_ENDPOINT="${DB_ENDPOINT}"
DB_PASSWORD="${DB_PASSWORD}"
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
S3_BUCKET="${S3_BUCKET}"
AWS_REGION="${AWS_REGION}"

# Log everything
exec > >(tee /var/log/user-data.log) 2>&1
echo "=== AWSNoc IA IA Setup Started at $(date) ==="

# Update system
apt-get update
apt-get upgrade -y

# Install essential packages
apt-get install -y python3.11 python3.11-venv python3-pip postgresql-client git nginx curl unzip awscli

# Create application directory
mkdir -p /opt/awsnoc-ia
chown ubuntu:ubuntu /opt/awsnoc-ia
cd /opt/awsnoc-ia

# Create environment file
cat > /opt/awsnoc-ia/.env << EOF
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_ENDPOINT}/${DB_NAME}
AWS_REGION=${AWS_REGION}
S3_BUCKET=${S3_BUCKET}
DEBUG=True
HOST=0.0.0.0
PORT=8000
EOF

chown ubuntu:ubuntu /opt/awsnoc-ia/.env

# Create dirs
sudo -u ubuntu mkdir -p /opt/awsnoc-ia/{backend,frontend/dist}

# Download setup from S3 (we'll upload it later)
echo "AWSNoc IA IA Development Environment Ready" > /opt/awsnoc-ia/frontend/dist/index.html

# Setup complete
echo "=== Setup completed at $(date) ==="
echo "Ready for deployment"

