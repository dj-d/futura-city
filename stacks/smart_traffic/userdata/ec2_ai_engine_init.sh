#!/bin/bash

WORKING_DIR="/mnt/repos"

# Install dependencies
sudo yum update -y
sudo yum install -y git
sudo yum install -y jq
sudo yum install -y python3

# Create working directory
mkdir -p  "$WORKING_DIR"
cd "$WORKING_DIR"

# Get GitHub token
GITHUB_TOKEN=$(aws secretsmanager get-secret-value --secret-id $GH_TOKEN_ID | jq --raw-output .SecretString | jq -r .'"github-token"')

# Clone repo
if [ ! -d "fc-st-ec2-ai-engine" ]; then
  git clone https://dj-d:"$GITHUB_TOKEN"@github.com/dj-d/fc-st-ec2-ai-engine
fi