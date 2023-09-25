#!/bin/bash

WORKING_DIR="/mnt/repos"

# Install dependencies
sudo yum update -y
sudo yum install -y git
sudo yum install -y jq
sudo yum install -y python3
sudo yum install -y python3-pip
sudo yum install -y make

# Create working directory
mkdir -p  "$WORKING_DIR"
cd "$WORKING_DIR" || echo "Failed to change directory" >> "$WORKING_DIR"/error.log

# Clone repo
if [ ! -d "da-ec2" ]; then
  # Get GitHub token
  GITHUB_TOKEN=$(aws secretsmanager get-secret-value --secret-id "$GH_TOKEN_ID" | jq --raw-output .SecretString | jq -r .'"github-token"')

  git clone https://dj-d:"$GITHUB_TOKEN"@github.com/dj-d/da-ec2 \
  && sleep 5 \
  && cd "$WORKING_DIR"/da-ec2 \
  && make install-dep \
  && cd .. \
  && touch 'done' \
  || echo "Failed to clone repo" >> "$WORKING_DIR"/error.log && exit 1
fi

while [ ! -f 'done' ]; do
  sleep 5
done

cd "$WORKING_DIR"/da-ec2 || echo "Failed to change directory" >> "$WORKING_DIR"/error.log && exit 1

touch "$WORKING_DIR"/da-ec2/test.txt

nohup make local-dev >/dev/null 2>&1 &