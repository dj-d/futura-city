#!/bin/bash

WORKING_DIR="/tmp/repos"

# Install dependencies
yum update -y
yum install -y git
yum install -y jq
yum install -y python3
yum install -y python3-pip
yum install -y make

echo "1" >> "$WORKING_DIR"/status.log

# Create working directory
mkdir -p  "$WORKING_DIR"
cd "$WORKING_DIR" || echo "Failed to change directory" >> "$WORKING_DIR"/error.log

echo "2" >> "$WORKING_DIR"/status.log

# Clone repo
if [ ! -d "da-ec2" ]; then
  # Get GitHub token
  GITHUB_TOKEN=$(aws secretsmanager get-secret-value --secret-id "$GH_TOKEN_ID" | jq --raw-output .SecretString | jq -r .'"github-token"')

  echo "3" >> "$WORKING_DIR"/status.log

  git clone https://dj-d:"$GITHUB_TOKEN"@github.com/dj-d/da-ec2

  echo "4" >> "$WORKING_DIR"/status.log
fi

if [ -d "$WORKING_DIR/da-ec2" ]; then
  echo "5" >> "$WORKING_DIR"/status.log

  cd "$WORKING_DIR"/da-ec2

  echo "6" >> "$WORKING_DIR"/status.log

  touch test.txt

  echo "7" >> "$WORKING_DIR"/status.log

  chown -R ec2-user:ec2-user "$WORKING_DIR"

  echo "8" >> "$WORKING_DIR"/status.log

  su ec2-user -c echo "export S3_BUCKET=$S3_BUCKET" >> /home/ec2-user/.bash_profile

  su ec2-user -c make install-dep

  echo "9" >> "$WORKING_DIR"/status.log

  su ec2-user -c nohup make local-dev >>"$WORKING_DIR"/be.log 2>>"$WORKING_DIR"/error.log &

  echo "10" >> "$WORKING_DIR"/status.log
else
  echo "Failed to clone repo" >> "$WORKING_DIR"/error.log
  exit 1
fi
