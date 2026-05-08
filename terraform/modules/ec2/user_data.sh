#!/bin/bash
set -euo pipefail

# Install Docker via amazon-linux-extras
yum update -y
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker

# Allow ec2-user to run docker without sudo
usermod -aG docker ec2-user

# Install Docker Compose v2 plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
